"""Test Attempt execution, observation, calculation, compliance, and trace REST API endpoints."""

from typing import Any, Dict, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.metrology import Calculation, ComplianceResult, Evidence
from app.models.test_execution import Observation, TestAttempt
from app.schemas.metrology import CalculationRead, ComplianceResultRead, EvidenceCreate, EvidenceRead
from app.schemas.test_execution import ObservationCreate, ObservationRead, TestAttemptRead, TestStepRead
from app.services.calculation_service import execute_attempt_calculation
from app.services.test_service import complete_test_attempt, get_test_attempt, record_observation, ObservationLockedError
from app.services.trace_service import get_test_attempt_trace

router = APIRouter(tags=["Test Attempts"])


@router.get("/test-attempts/{attempt_id}", response_model=TestAttemptRead)
def get_attempt(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> TestAttemptRead:
    """Retrieve details of a test attempt including procedural steps and observations."""
    att = get_test_attempt(db, attempt_id)
    if not att:
        raise HTTPException(status_code=404, detail="Test attempt not found")

    steps_data = [TestStepRead.model_validate(s) for s in att.steps]
    obs_data = [ObservationRead.model_validate(o) for o in att.observations]

    return TestAttemptRead(
        id=att.id,
        evaluation_test_id=att.evaluation_test_id,
        attempt_number=att.attempt_number,
        status=att.status,
        started_at=att.started_at,
        completed_at=att.completed_at,
        supersedes_attempt_id=att.supersedes_attempt_id,
        notes=att.notes,
        steps=steps_data,
        observations=obs_data,
    )


@router.post("/test-attempts/{attempt_id}/complete", response_model=TestAttemptRead)
def complete_attempt(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> TestAttemptRead:
    """Mark an execution attempt as completed."""
    try:
        att = complete_test_attempt(db, attempt_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    steps_data = [TestStepRead.model_validate(s) for s in att.steps]
    obs_data = [ObservationRead.model_validate(o) for o in att.observations]
    return TestAttemptRead(
        id=att.id,
        evaluation_test_id=att.evaluation_test_id,
        attempt_number=att.attempt_number,
        status=att.status,
        started_at=att.started_at,
        completed_at=att.completed_at,
        supersedes_attempt_id=att.supersedes_attempt_id,
        notes=att.notes,
        steps=steps_data,
        observations=obs_data,
    )


@router.post(
    "/test-attempts/{attempt_id}/observations",
    response_model=ObservationRead,
    status_code=status.HTTP_201_CREATED,
)
def submit_observation(
    attempt_id: uuid.UUID,
    payload: ObservationCreate,
    db: Session = Depends(get_db),
) -> ObservationRead:
    """Record a raw laboratory measurement for a test attempt."""
    try:
        obs = record_observation(
            db=db,
            attempt_id=attempt_id,
            observation_code=payload.observation_code,
            value_numeric=payload.value_numeric,
            value_text=payload.value_text,
            unit=payload.unit,
            value_json=payload.value_json,
            test_step_id=payload.test_step_id,
            entered_by=payload.entered_by,
            notes=payload.notes,
        )
    except ObservationLockedError as exc:
        raise HTTPException(
            status_code=409,
            detail={"error_code": "OBSERVATION_LOCKED", "message": str(exc)},
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error_code": "VALIDATION_ERROR", "message": str(exc)},
        )
    return ObservationRead.model_validate(obs)


@router.get("/test-attempts/{attempt_id}/observations", response_model=List[ObservationRead])
def list_observations(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[ObservationRead]:
    """List all raw observations recorded for a test attempt."""
    att = get_test_attempt(db, attempt_id)
    if not att:
        raise HTTPException(status_code=404, detail="Test attempt not found")
    return [ObservationRead.model_validate(o) for o in att.observations]


@router.post("/test-attempts/{attempt_id}/calculate", response_model=Dict[str, Any])
def run_calculation(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Execute authoritative R-76 calculations and compliance evaluation for a test attempt."""
    try:
        result = execute_attempt_calculation(db, attempt_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "CALCULATION_ERROR", "message": str(exc)},
        )
    return result


@router.get("/test-attempts/{attempt_id}/calculations", response_model=List[CalculationRead])
def list_calculations(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[CalculationRead]:
    """List calculation history for a test attempt."""
    calcs = db.scalars(
        select(Calculation).where(Calculation.test_attempt_id == attempt_id)
    ).all()
    return [CalculationRead.model_validate(c) for c in calcs]


@router.get("/test-attempts/{attempt_id}/result", response_model=ComplianceResultRead)
def get_compliance_result(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ComplianceResultRead:
    """Retrieve the latest compliance result for a test attempt."""
    comp = db.scalar(
        select(ComplianceResult)
        .where(ComplianceResult.test_attempt_id == attempt_id)
        .order_by(ComplianceResult.decided_at.desc())
        .limit(1)
    )
    if not comp:
        raise HTTPException(status_code=404, detail="No compliance result available for this attempt")
    return ComplianceResultRead.model_validate(comp)


@router.get("/test-attempts/{attempt_id}/trace", response_model=Dict[str, Any])
def get_attempt_trace(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve the complete audit traceability chain: Decision -> Criterion -> RuleVersion -> Calculation -> Observations -> Instrument."""
    try:
        trace = get_test_attempt_trace(db, attempt_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return trace


@router.post(
    "/test-attempts/{attempt_id}/evidence",
    response_model=EvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_attempt_evidence(
    attempt_id: uuid.UUID,
    payload: EvidenceCreate,
    db: Session = Depends(get_db),
) -> EvidenceRead:
    """Attach evidence artifact metadata to a test attempt."""
    att = get_test_attempt(db, attempt_id)
    if not att:
        raise HTTPException(status_code=404, detail="Test attempt not found")

    eval_id = att.evaluation_test.evaluation_id
    ev = Evidence(
        evaluation_id=eval_id,
        test_attempt_id=attempt_id,
        evidence_type=payload.evidence_type,
        filename=payload.filename,
        storage_key=payload.storage_key,
        sha256=payload.sha256,
        metadata_json=payload.metadata_json,
        uploaded_by=payload.uploaded_by,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return EvidenceRead.model_validate(ev)
