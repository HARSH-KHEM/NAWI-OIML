"""Service managing test attempts, retests, and raw observation recording."""

from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.engines.mpe import convert_mass
from app.models.metrology import AuditEvent, Calculation, ComplianceResult
from app.models.test_execution import (
    EvaluationTest,
    EvaluationTestStatus,
    Observation,
    TestAttempt,
    TestAttemptStatus,
    TestStep,
)
from app.schemas.test_execution import (
    EccentricityObservationPayload,
    RepeatabilityObservationPayload,
)
from app.services.plan_service import create_initial_steps_for_attempt

logger = logging.getLogger(__name__)


class ObservationLockedError(ValueError):
    """Raised when attempting to add or modify observations on a locked TestAttempt."""
    pass


def get_evaluation_test(db: Session, test_id: uuid.UUID) -> Optional[EvaluationTest]:
    """Retrieve an evaluation test by ID."""
    return db.get(EvaluationTest, test_id)


def get_test_attempt(db: Session, attempt_id: uuid.UUID) -> Optional[TestAttempt]:
    """Retrieve a test attempt by ID."""
    return db.get(TestAttempt, attempt_id)


def create_retest_attempt(
    db: Session,
    test_id: uuid.UUID,
    notes: Optional[str] = None,
    actor_id: Optional[str] = None,
) -> TestAttempt:
    """Create a new test attempt for an evaluation test without overwriting previous attempts.
    
    Retest requirement: Attempt 1 remains permanently in history (e.g. status SUPERSEDED or COMPLETED with its FAIL result),
    while Attempt 2 receives new observations and fresh calculations.
    """
    eval_test = db.get(EvaluationTest, test_id)
    if not eval_test:
        raise ValueError(f"EvaluationTest {test_id} not found")

    # Mark active attempt as superseded
    prev_attempt = db.scalar(
        select(TestAttempt)
        .where(
            TestAttempt.evaluation_test_id == test_id,
            TestAttempt.status == TestAttemptStatus.ACTIVE,
        )
        .order_by(TestAttempt.attempt_number.desc())
    )

    next_num = 1
    superseded_id = None
    if prev_attempt:
        prev_attempt.status = TestAttemptStatus.SUPERSEDED
        next_num = prev_attempt.attempt_number + 1
        superseded_id = prev_attempt.id

    new_attempt = TestAttempt(
        evaluation_test_id=eval_test.id,
        attempt_number=next_num,
        status=TestAttemptStatus.ACTIVE,
        supersedes_attempt_id=superseded_id,
        notes=notes,
    )
    db.add(new_attempt)
    db.flush()

    # Create procedural steps
    create_initial_steps_for_attempt(db, eval_test, new_attempt)

    # Record audit event
    audit_evt = AuditEvent(
        evaluation_id=eval_test.evaluation_id,
        entity_type="TEST_ATTEMPT",
        entity_id=new_attempt.id,
        action="RETEST_ATTEMPT_CREATED",
        actor_id=actor_id,
        metadata_json={
            "attempt_number": next_num,
            "supersedes_attempt_id": str(superseded_id) if superseded_id else None,
            "test_code": eval_test.test_definition.test_code,
        },
    )
    db.add(audit_evt)
    db.commit()
    db.refresh(new_attempt)
    return new_attempt


def record_observation(
    db: Session,
    attempt_id: uuid.UUID,
    observation_code: str,
    value_numeric: Optional[Decimal] = None,
    value_text: Optional[str] = None,
    unit: Optional[str] = None,
    value_json: Optional[Dict[str, Any]] = None,
    test_step_id: Optional[uuid.UUID] = None,
    entered_by: Optional[str] = None,
    notes: Optional[str] = None,
) -> Observation:
    """Record a raw laboratory observation for a test attempt.
    
    Performs strict domain validation and enforces observation locking.
    """
    attempt = db.get(TestAttempt, attempt_id)
    if not attempt:
        raise ValueError(f"TestAttempt {attempt_id} not found")

    # Invariant: Observations for an attempt are locked once calculation or compliance exists
    has_calcs = db.scalar(
        select(Calculation.id).where(Calculation.test_attempt_id == attempt.id).limit(1)
    ) is not None
    has_comps = db.scalar(
        select(ComplianceResult.id).where(ComplianceResult.test_attempt_id == attempt.id).limit(1)
    ) is not None

    if has_calcs or has_comps or attempt.calculations or attempt.compliance_results:
        raise ObservationLockedError(
            f"TestAttempt {attempt_id} is locked because calculations or compliance results already exist. "
            "Observations cannot be added or modified on a locked attempt. Create a new TestAttempt (retest) instead."
        )

    eval_test = attempt.evaluation_test
    eval_snapshot = eval_test.evaluation.configuration_snapshot or {}
    test_code = eval_test.test_definition.test_code if eval_test.test_definition else ""

    # 1. Strict Repeatability payload validation
    if "REPEATABILITY" in test_code or (value_json and "series" in value_json):
        if not value_json:
            raise ValueError(
                "Repeatability observation requires structured value_json with "
                "series, weighing_index, test_load, loaded_indication, unloaded_indication"
            )
        try:
            rep_payload = RepeatabilityObservationPayload(**value_json)
        except Exception as e:
            raise ValueError(f"Invalid repeatability observation payload: {e}")

        # Ensure weighing_index is unique within series for this attempt
        existing_obs_list = db.scalars(
            select(Observation).where(Observation.test_attempt_id == attempt.id)
        ).all()
        for existing_obs in existing_obs_list:
            if existing_obs.value_json and existing_obs.value_json.get("series") == rep_payload.series.value:
                if int(existing_obs.value_json.get("weighing_index", -1)) == rep_payload.weighing_index:
                    raise ValueError(
                        f"Duplicate weighing_index {rep_payload.weighing_index} for series {rep_payload.series.value} in attempt {attempt_id}"
                    )

        value_json = {
            "series": rep_payload.series.value,
            "weighing_index": rep_payload.weighing_index,
            "test_load": str(rep_payload.test_load),
            "loaded_indication": str(rep_payload.loaded_indication),
            "unloaded_indication": str(rep_payload.unloaded_indication),
            "unit": rep_payload.unit or unit,
        }
        if value_numeric is None:
            value_numeric = rep_payload.loaded_indication

    # 2. Strict Eccentricity payload validation
    elif "ECCENTRICITY" in test_code or (value_json and "position" in value_json) or observation_code.upper().startswith("POS_"):
        if value_json and "position" in value_json:
            try:
                ecc_payload = EccentricityObservationPayload(**value_json)
            except Exception as e:
                raise ValueError(f"Invalid eccentricity observation payload: {e}")

            pos_val = str(ecc_payload.position).upper()

            # Ensure position is unique within this attempt
            existing_obs_list = db.scalars(
                select(Observation).where(Observation.test_attempt_id == attempt.id)
            ).all()
            for existing_obs in existing_obs_list:
                existing_pos = existing_obs.value_json.get("position") if existing_obs.value_json else None
                if not existing_pos and existing_obs.observation_code.startswith("POS_"):
                    existing_pos = existing_obs.observation_code.replace("POS_", "")
                if existing_pos and existing_pos.upper() == pos_val:
                    raise ValueError(
                        f"Duplicate eccentricity position: {pos_val} in attempt {attempt_id}"
                    )

            value_json = {
                "position": pos_val,
            }
            if ecc_payload.load is not None:
                value_json["load"] = str(ecc_payload.load)
            if ecc_payload.indication is not None:
                value_json["indication"] = str(ecc_payload.indication)
            if ecc_payload.additional_load is not None:
                value_json["additional_load"] = str(ecc_payload.additional_load)
            if ecc_payload.zero_error is not None:
                value_json["zero_error"] = str(ecc_payload.zero_error)
            if ecc_payload.unit or unit:
                value_json["unit"] = ecc_payload.unit or unit
            if value_numeric is None and ecc_payload.indication is not None:
                value_numeric = ecc_payload.indication

    # 3. Domain validation against snapshot Max capacity
    if observation_code.upper() in ("LOAD", "TARGET_LOAD") and value_numeric is not None:
        if value_numeric <= Decimal("0"):
            raise ValueError(f"Observed load must be strictly positive, got {value_numeric}")
        
        # Determine authoritative configuration/range unit
        if eval_test.range_index is not None and eval_snapshot.get("ranges"):
            matching_range = next(
                (r for r in eval_snapshot["ranges"] if int(r["range_index"]) == eval_test.range_index),
                None,
            )
            if not matching_range:
                raise ValueError(f"Range index {eval_test.range_index} not found in configuration snapshot ranges")
            max_cap = Decimal(str(matching_range["max_capacity"]))
            e_val = Decimal(str(matching_range["verification_scale_interval"]))
            target_unit = str(matching_range.get("unit", eval_snapshot.get("unit", "kg"))).lower()
        else:
            if "max_capacity" not in eval_snapshot or "verification_scale_interval" not in eval_snapshot:
                raise ValueError("Configuration snapshot missing required max_capacity or verification_scale_interval")
            max_cap = Decimal(str(eval_snapshot["max_capacity"]))
            e_val = Decimal(str(eval_snapshot["verification_scale_interval"]))
            target_unit = str(eval_snapshot.get("unit", "kg")).lower()

        # Validate supplied unit
        obs_unit = (unit or (value_json.get("unit") if value_json else None) or target_unit).lower()

        # Normalize value before Max validation
        try:
            normalized_load = convert_mass(value_numeric, from_unit=obs_unit, to_unit=target_unit)
        except Exception as exc:
            raise ValueError(f"Invalid unit or unit conversion failed: {exc}")

        # R-76 allows loading slightly above Max (e.g. Max + 9e before saturation/error), but not wildly excessive
        overload_limit = max_cap + (Decimal("9") * e_val)
        if normalized_load > overload_limit:
            raise ValueError(
                f"Observed load {value_numeric} {obs_unit} (normalized: {normalized_load} {target_unit}) exceeds allowable range limit (Max={max_cap} {target_unit}, overload limit={overload_limit} {target_unit})"
            )


    obs = Observation(
        test_attempt_id=attempt.id,
        test_step_id=test_step_id,
        observation_code=observation_code.upper(),
        value_numeric=value_numeric,
        value_text=value_text,
        unit=unit,
        value_json=value_json,
        entered_by=entered_by,
        validation_status="VALID",
        notes=notes,
    )
    db.add(obs)
    db.flush()

    # Record audit event
    audit_evt = AuditEvent(
        evaluation_id=eval_test.evaluation_id,
        entity_type="OBSERVATION",
        entity_id=obs.id,
        action="OBSERVATION_RECORDED",
        actor_id=entered_by,
        metadata_json={
            "attempt_id": str(attempt.id),
            "code": obs.observation_code,
            "value_numeric": str(obs.value_numeric) if obs.value_numeric is not None else None,
            "unit": obs.unit,
        },
    )
    db.add(audit_evt)
    db.commit()

    return obs


def update_observation(
    db: Session,
    observation_id: uuid.UUID,
    value_numeric: Optional[Decimal] = None,
    value_text: Optional[str] = None,
    notes: Optional[str] = None,
    actor_id: Optional[str] = None,
) -> Observation:
    """Update an existing observation with complete audit trail.
    
    Enforces observation locking: cannot modify if attempt has calculations/compliance results.
    """
    obs = db.get(Observation, observation_id)
    if not obs:
        raise ValueError(f"Observation {observation_id} not found")

    attempt = obs.test_attempt
    has_calcs = db.scalar(
        select(Calculation.id).where(Calculation.test_attempt_id == attempt.id).limit(1)
    ) is not None
    has_comps = db.scalar(
        select(ComplianceResult.id).where(ComplianceResult.test_attempt_id == attempt.id).limit(1)
    ) is not None

    if has_calcs or has_comps or attempt.calculations or attempt.compliance_results:
        raise ObservationLockedError(
            f"Observation {observation_id} cannot be modified because its TestAttempt {attempt.id} is locked. "
            "Create a new TestAttempt (retest) to record corrected observations."
        )

    before = {
        "value_numeric": str(obs.value_numeric) if obs.value_numeric is not None else None,
        "value_text": obs.value_text,
        "notes": obs.notes,
    }

    if value_numeric is not None:
        obs.value_numeric = value_numeric
    if value_text is not None:
        obs.value_text = value_text
    if notes is not None:
        obs.notes = notes

    after = {
        "value_numeric": str(obs.value_numeric) if obs.value_numeric is not None else None,
        "value_text": obs.value_text,
        "notes": obs.notes,
    }

    eval_id = obs.test_attempt.evaluation_test.evaluation_id
    audit_evt = AuditEvent(
        evaluation_id=eval_id,
        entity_type="OBSERVATION",
        entity_id=obs.id,
        action="OBSERVATION_UPDATED",
        actor_id=actor_id,
        before_json=before,
        after_json=after,
    )
    db.add(audit_evt)
    db.commit()
    return obs


def complete_test_attempt(
    db: Session,
    attempt_id: uuid.UUID,
    actor_id: Optional[str] = None,
) -> TestAttempt:
    """Mark a test attempt as completed."""
    attempt = db.get(TestAttempt, attempt_id)
    if not attempt:
        raise ValueError(f"TestAttempt {attempt_id} not found")

    attempt.status = TestAttemptStatus.COMPLETED
    attempt.completed_at = func.now()

    eval_id = attempt.evaluation_test.evaluation_id
    audit_evt = AuditEvent(
        evaluation_id=eval_id,
        entity_type="TEST_ATTEMPT",
        entity_id=attempt.id,
        action="TEST_COMPLETED",
        actor_id=actor_id,
    )
    db.add(audit_evt)
    db.commit()
    return attempt
