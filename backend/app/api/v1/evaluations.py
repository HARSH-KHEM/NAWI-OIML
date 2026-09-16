"""Evaluation and test plan REST API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.configuration import InstrumentConfiguration
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.instrument import Instrument
from app.models.metrology import AuditEvent
from app.models.rule import RuleVersion
from app.models.test_execution import EvaluationTest, EvaluationTestStatus
from app.schemas.evaluation import EvaluationCreate, EvaluationPlanResponse, EvaluationRead, EvaluationReportResponse
from app.schemas.test_execution import EvaluationTestRead
from app.services.plan_service import generate_evaluation_plan
from app.services.report_service import generate_evaluation_report

router = APIRouter(tags=["Evaluations"])


@router.post(
    "/instruments/{instrument_id}/evaluations",
    response_model=EvaluationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_evaluation(
    instrument_id: uuid.UUID,
    payload: EvaluationCreate,
    db: Session = Depends(get_db),
) -> Evaluation:
    """Initialize a new R-76 Type Evaluation and capture an immutable configuration snapshot."""
    inst = db.get(Instrument, instrument_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")

    # Resolve configuration to snapshot
    if payload.instrument_configuration_id:
        config = db.get(InstrumentConfiguration, payload.instrument_configuration_id)
        if not config or config.instrument_id != instrument_id:
            raise HTTPException(status_code=404, detail="Specified instrument configuration not found")
    else:
        # Pick latest active configuration
        config = db.scalar(
            select(InstrumentConfiguration)
            .where(InstrumentConfiguration.instrument_id == instrument_id, InstrumentConfiguration.is_active.is_(True))
            .order_by(InstrumentConfiguration.created_at.desc())
            .limit(1)
        )
        if not config:
            raise HTTPException(
                status_code=400,
                detail="Instrument has no configured metrological specification. Create a configuration first.",
            )

    # Resolve rule version
    if payload.rule_version_id:
        rule_ver = db.get(RuleVersion, payload.rule_version_id)
        if not rule_ver:
            raise HTTPException(status_code=404, detail="Specified rule version not found")
    else:
        rule_ver = db.scalar(select(RuleVersion).where(RuleVersion.is_active.is_(True)).limit(1))
        if not rule_ver:
            rule_ver = db.scalar(select(RuleVersion).limit(1))
        if not rule_ver:
            raise HTTPException(status_code=500, detail="No active RuleVersion found in database")

    # Serialize immutable snapshot of configuration (including ranges if multi-range)
    ranges_snapshot = [
        {
            "range_index": r.range_index,
            "min_capacity": str(r.min_capacity),
            "max_capacity": str(r.max_capacity),
            "verification_scale_interval": str(r.verification_scale_interval),
            "actual_scale_interval": str(r.actual_scale_interval),
            "unit": r.unit,
        }
        for r in config.ranges
    ]

    snapshot = {
        "accuracy_class": config.accuracy_class.value,
        "max_capacity": str(config.max_capacity),
        "min_capacity": str(config.min_capacity),
        "verification_scale_interval": str(config.verification_scale_interval),
        "actual_scale_interval": str(config.actual_scale_interval),
        "unit": config.unit,
        "number_of_ranges": config.number_of_ranges,
        "is_multiple_range": config.is_multiple_range,
        "tare_type": config.tare_type.value,
        "is_electronic": config.is_electronic,
        "has_zero_setting": config.has_zero_setting,
        "extra_capabilities": config.extra_capabilities,
        "ranges": ranges_snapshot,
        "snapshot_timestamp": datetime.utcnow().isoformat(),
        "instrument_serial": inst.serial_number,
        "manufacturer": inst.manufacturer,
        "model_name": inst.model_name,
    }

    eval_num = payload.evaluation_number or f"EVAL-{uuid.uuid4().hex[:8].upper()}"

    eval_record = Evaluation(
        evaluation_number=eval_num,
        instrument_id=inst.id,
        instrument_configuration_id=config.id,
        rule_version_id=rule_ver.id,
        configuration_snapshot=snapshot,
        status=EvaluationStatus.IN_PROGRESS,
        operator_id=payload.operator_id,
        lab_name=payload.lab_name,
    )
    db.add(eval_record)
    db.flush()

    audit = AuditEvent(
        evaluation_id=eval_record.id,
        entity_type="EVALUATION",
        entity_id=eval_record.id,
        action="EVALUATION_CREATED",
        metadata_json={"evaluation_number": eval_record.evaluation_number},
    )
    db.add(audit)
    db.commit()
    db.refresh(eval_record)
    return eval_record


@router.get("/evaluations", response_model=List[EvaluationRead])
def list_evaluations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[Evaluation]:
    """List all evaluations in reverse chronological order."""
    return db.scalars(
        select(Evaluation)
        .order_by(Evaluation.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationRead)
def get_evaluation(
    evaluation_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Evaluation:
    """Retrieve an evaluation by ID."""
    eval_rec = db.get(Evaluation, evaluation_id)
    if not eval_rec:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return eval_rec

def _to_test_read(t: EvaluationTest) -> EvaluationTestRead:
    effective_code = (
        f"{t.test_definition.test_code}_{t.range_reference}"
        if t.range_reference and t.scope_type == "RANGE"
        else t.test_definition.test_code
    )
    effective_title = (
        f"{t.test_definition.title} — {t.range_reference.replace('_', ' ').title()}"
        if t.range_reference and t.scope_type == "RANGE"
        else t.test_definition.title
    )
    return EvaluationTestRead(
        id=t.id,
        evaluation_id=t.evaluation_id,
        test_definition_id=t.test_definition_id,
        rule_version_id=t.rule_version_id,
        sequence=t.sequence,
        status=t.status,
        scope_type=t.scope_type,
        range_reference=t.range_reference,
        range_index=t.range_index,
        applicability_reason=t.applicability_reason,
        implementation_status=t.implementation_status,
        test_code=effective_code,
        title=effective_title,
        r76_reference=t.test_definition.r76_reference,
    )


@router.post("/evaluations/{evaluation_id}/generate-plan", response_model=EvaluationPlanResponse)
def generate_plan_endpoint(
    evaluation_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> EvaluationPlanResponse:
    """Generate an authoritative, deterministic test plan from the frozen configuration snapshot."""
    eval_rec = db.get(Evaluation, evaluation_id)
    if not eval_rec:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    try:
        tests = generate_evaluation_plan(db, evaluation_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    test_reads = [_to_test_read(t) for t in tests]

    return EvaluationPlanResponse(
        evaluation_id=eval_rec.id,
        evaluation_number=eval_rec.evaluation_number,
        status=eval_rec.status,
        configuration_snapshot=eval_rec.configuration_snapshot,
        tests=test_reads,
        total_tests=len(test_reads),
        applicable_tests_count=sum(1 for t in tests if t.status != EvaluationTestStatus.NOT_APPLICABLE),
    )


@router.get("/evaluations/{evaluation_id}/plan", response_model=EvaluationPlanResponse)
def get_evaluation_plan(
    evaluation_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> EvaluationPlanResponse:
    """Retrieve the generated test plan for an evaluation."""
    eval_rec = db.get(Evaluation, evaluation_id)
    if not eval_rec:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    tests = db.scalars(
        select(EvaluationTest)
        .where(EvaluationTest.evaluation_id == evaluation_id)
        .order_by(EvaluationTest.sequence)
    ).all()

    test_reads = [_to_test_read(t) for t in tests]

    return EvaluationPlanResponse(
        evaluation_id=eval_rec.id,
        evaluation_number=eval_rec.evaluation_number,
        status=eval_rec.status,
        configuration_snapshot=eval_rec.configuration_snapshot,
        tests=test_reads,
        total_tests=len(test_reads),
        applicable_tests_count=sum(1 for t in tests if t.status != EvaluationTestStatus.NOT_APPLICABLE),
    )


@router.get("/evaluations/{evaluation_id}/tests", response_model=List[EvaluationTestRead])
def list_evaluation_tests(
    evaluation_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[EvaluationTestRead]:
    """List all instantiated tests for an evaluation."""
    tests = db.scalars(
        select(EvaluationTest)
        .where(EvaluationTest.evaluation_id == evaluation_id)
        .order_by(EvaluationTest.sequence)
    ).all()

    return [_to_test_read(t) for t in tests]


@router.get("/evaluations/{evaluation_id}/report", response_model=EvaluationReportResponse)
def get_evaluation_report_endpoint(
    evaluation_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve an authoritative OIML R-76 technical evaluation report."""
    try:
        return generate_evaluation_report(db, evaluation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

