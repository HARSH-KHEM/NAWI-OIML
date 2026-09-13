"""Service generating executable R-76 test plans from frozen configuration snapshots."""

from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.applicability import ApplicabilityEngine, ApplicableTestItem
from app.models.evaluation import Evaluation
from app.models.metrology import AuditEvent
from app.models.rule import RuleVersion
from app.models.test_definition import ImplementationStatus, ScopeType, TestDefinition
from app.models.test_execution import (
    EvaluationTest,
    EvaluationTestStatus,
    TestAttempt,
    TestAttemptStatus,
    TestStep,
    TestStepStatus,
)

logger = logging.getLogger(__name__)


def ensure_test_definitions(db: Session) -> Dict[str, TestDefinition]:
    """Ensure canonical test definitions exist in the database."""
    existing = db.scalars(select(TestDefinition)).all()
    defs_by_code = {td.test_code: td for td in existing}

    canonical_defs = [
        ("WEIGHING_PERFORMANCE", "Weighing Performance", "A.4.4", ImplementationStatus.IMPLEMENTED, ScopeType.INSTRUMENT, 10),
        ("ECCENTRICITY", "Eccentricity Test", "A.4.7", ImplementationStatus.IMPLEMENTED, ScopeType.INSTRUMENT, 20),
        ("REPEATABILITY", "Repeatability Test", "A.4.10", ImplementationStatus.IMPLEMENTED, ScopeType.INSTRUMENT, 30),
        ("TARE", "Tare Balancing & Weighing", "A.4.6", ImplementationStatus.PARTIAL, ScopeType.INSTRUMENT, 40),
        ("ZERO_SETTING", "Zero-Setting Range & Accuracy", "A.4.2", ImplementationStatus.APPLICABILITY_ONLY, ScopeType.INSTRUMENT, 50),
        ("CREEP", "Creep Test", "3.9.4.1 / A.4.11.1", ImplementationStatus.APPLICABILITY_ONLY, ScopeType.INSTRUMENT, 60),
        ("TEMPERATURE", "Static Temperatures Test", "A.5.3.1", ImplementationStatus.APPLICABILITY_ONLY, ScopeType.INSTRUMENT, 70),
        ("VOLTAGE_VARIATION", "Voltage Variations Test", "A.5.4", ImplementationStatus.APPLICABILITY_ONLY, ScopeType.INSTRUMENT, 80),
        ("WARM_UP", "Warm-up Test", "A.5.2", ImplementationStatus.APPLICABILITY_ONLY, ScopeType.INSTRUMENT, 90),
        ("ENDURANCE", "Endurance Test", "3.9.4.3 & A.6", ImplementationStatus.APPLICABILITY_ONLY, ScopeType.INSTRUMENT, 100),
    ]

    for code, title, ref, status, scope, seq in canonical_defs:
        if code not in defs_by_code:
            td = TestDefinition(
                test_code=code,
                title=title,
                r76_reference=ref,
                implementation_status=status,
                scope_type=scope,
                sequence=seq,
                is_active=True,
            )
            db.add(td)
            db.flush()
            defs_by_code[code] = td

    return defs_by_code


def create_initial_steps_for_attempt(db: Session, test: EvaluationTest, attempt: TestAttempt):
    """Create standard procedural steps for an instantiated test attempt."""
    base_code = test.test_definition.test_code

    if "WEIGHING_PERFORMANCE" in base_code:
        # Step 1: Zero error determination
        step1 = TestStep(
            test_attempt_id=attempt.id,
            step_code="STEP_ZERO_ERROR",
            sequence=1,
            title="Determine Zero Error (E0)",
            instruction="With no load on the receptor, place additional weights to determine changeover point and calculate zero error E0 (clause A.4.2.3 / A.4.4.3).",
            status=TestStepStatus.PENDING,
            required=True,
            metadata_json={"observation_keys": ["LOAD", "INDICATION", "ADDITIONAL_LOAD"]},
        )
        # Step 2: Test load points
        step2 = TestStep(
            test_attempt_id=attempt.id,
            step_code="STEP_LOADING_POINTS",
            sequence=2,
            title="Apply Test Loads and Record Indications",
            instruction="Apply test loads in increasing order (including Min, MPE changeover points, and Max). Record indication I and additional load ΔL.",
            status=TestStepStatus.PENDING,
            required=True,
            metadata_json={"range_reference": test.range_reference},
        )
        db.add_all([step1, step2])

    elif base_code == "ECCENTRICITY":
        # Resolve configuration-driven eccentricity procedure and load
        snapshot = test.evaluation.configuration_snapshot if test.evaluation else None
        if not snapshot:
            ev = db.scalar(select(Evaluation).where(Evaluation.id == test.evaluation_id))
            snapshot = ev.configuration_snapshot if ev else {}

        from app.engines.applicability import (
            calculate_required_eccentricity_load,
            determine_eccentricity_procedure,
        )

        proc_info = determine_eccentricity_procedure(snapshot)
        if proc_info["status"] == "SUPPORTED":
            req_load = calculate_required_eccentricity_load(snapshot, proc_info)
            unit_val = str(snapshot.get("unit", "kg")).lower()
            positions = proc_info["positions"]
            seq = 1
            for pos in positions:
                db.add(
                    TestStep(
                        test_attempt_id=attempt.id,
                        step_code=f"STEP_{pos}",
                        sequence=seq,
                        title=f"Eccentricity Position: {pos}",
                        instruction=f"Apply eccentricity test load ({req_load} {unit_val}) at position {pos} according to procedure {proc_info['procedure']}.",
                        status=TestStepStatus.PENDING,
                        required=True,
                        metadata_json={
                            "procedure": proc_info["procedure"],
                            "position": pos,
                            "required_test_load": str(req_load),
                            "unit": unit_val,
                            "support_count": proc_info.get("support_count"),
                        },
                    )
                )
                seq += 1
        else:
            db.add(
                TestStep(
                    test_attempt_id=attempt.id,
                    step_code="STEP_ECCENTRICITY_BLOCKED",
                    sequence=1,
                    title="Eccentricity Test Blocked",
                    instruction=f"BLOCKED: {proc_info.get('reason', 'Missing geometry metadata')}",
                    status=TestStepStatus.BLOCKED,
                    required=True,
                    metadata_json={
                        "procedure": "UNSUPPORTED",
                        "reason": proc_info.get("reason"),
                    },
                )
            )

    elif base_code == "REPEATABILITY":
        step1 = TestStep(
            test_attempt_id=attempt.id,
            step_code="STEP_SERIES_50",
            sequence=1,
            title="Series 1: Load ≈ 50% Max",
            instruction="Perform repeated weighings with test load of approximately 50% Max (at least 10 weighings for Max < 1000 kg). Record indication between zero resets.",
            status=TestStepStatus.PENDING,
            required=True,
            metadata_json={"load_fraction": "0.50"},
        )
        step2 = TestStep(
            test_attempt_id=attempt.id,
            step_code="STEP_SERIES_100",
            sequence=2,
            title="Series 2: Load close to 100% Max",
            instruction="Perform repeated weighings with test load close to 100% Max. Record indication between zero resets.",
            status=TestStepStatus.PENDING,
            required=True,
            metadata_json={"load_fraction": "1.00"},
        )
        db.add_all([step1, step2])


def generate_evaluation_plan(db: Session, evaluation_id: uuid.UUID) -> List[EvaluationTest]:
    """Generate an authoritative, idempotent evaluation test plan based on the frozen configuration snapshot."""
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation:
        raise ValueError(f"Evaluation {evaluation_id} does not exist")

    # If plan has already been generated, return existing tests (idempotent behavior)
    existing_tests = db.scalars(
        select(EvaluationTest)
        .where(EvaluationTest.evaluation_id == evaluation_id)
        .order_by(EvaluationTest.sequence)
    ).all()
    if existing_tests:
        logger.info("Evaluation %s already has an active test plan; returning existing plan.", evaluation_id)
        return list(existing_tests)

    snapshot = evaluation.configuration_snapshot or {}
    if not snapshot:
        raise ValueError(f"Evaluation {evaluation_id} has no frozen configuration snapshot")

    # Ensure canonical definitions exist in catalog
    defs_by_code = ensure_test_definitions(db)

    # Resolve active RuleVersion
    rule_version_id = evaluation.rule_version_id
    if not rule_version_id:
        default_ver = db.scalar(select(RuleVersion).limit(1))
        if not default_ver:
            raise ValueError("No RuleVersion available to link evaluation tests")
        rule_version_id = default_ver.id

    # Evaluate plan via ApplicabilityEngine
    applicable_items = ApplicabilityEngine.evaluate_plan(snapshot)

    created_tests: List[EvaluationTest] = []

    for item in applicable_items:
        # Match test definition (strip range suffix if range-scoped)
        lookup_code = item.test_code
        if "_RANGE_" in lookup_code:
            lookup_code = lookup_code.split("_RANGE_")[0]

        test_def = defs_by_code.get(lookup_code)
        if not test_def:
            # Create definition if missing
            test_def = TestDefinition(
                test_code=lookup_code,
                title=item.title,
                r76_reference=item.r76_reference,
                implementation_status=item.implementation_status,
                scope_type=item.scope_type,
                sequence=item.sequence,
                is_active=True,
            )
            db.add(test_def)
            db.flush()
            defs_by_code[lookup_code] = test_def

        eval_test = EvaluationTest(
            evaluation_id=evaluation.id,
            test_definition_id=test_def.id,
            rule_version_id=rule_version_id,
            sequence=item.sequence,
            status=EvaluationTestStatus.NOT_STARTED if item.applicable else EvaluationTestStatus.NOT_APPLICABLE,
            scope_type=item.scope_type.value,
            range_reference=item.range_reference,
            range_index=item.range_index,
            applicability_reason=item.reason,
            implementation_status=item.implementation_status.value,
        )
        db.add(eval_test)
        db.flush()
        created_tests.append(eval_test)

        # For applicable & implemented tests, instantiate Attempt 1 and initial steps
        if item.applicable and item.implementation_status == ImplementationStatus.IMPLEMENTED:
            attempt = TestAttempt(
                evaluation_test_id=eval_test.id,
                attempt_number=1,
                status=TestAttemptStatus.ACTIVE,
            )
            db.add(attempt)
            db.flush()
            create_initial_steps_for_attempt(db, eval_test, attempt)

    # Record PLAN_GENERATED audit event
    audit_evt = AuditEvent(
        evaluation_id=evaluation.id,
        entity_type="EVALUATION",
        entity_id=evaluation.id,
        action="PLAN_GENERATED",
        metadata_json={
            "total_tests_generated": len(created_tests),
            "applicable_tests_count": sum(1 for t in created_tests if t.status != EvaluationTestStatus.NOT_APPLICABLE),
            "is_multiple_range": snapshot.get("is_multiple_range", False),
        },
    )
    db.add(audit_evt)
    db.commit()

    logger.info("Deterministic plan generated for evaluation %s: %d tests", evaluation.id, len(created_tests))
    return created_tests
