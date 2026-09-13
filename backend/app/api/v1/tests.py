"""Evaluation Tests and retesting REST API endpoints."""

from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.test_execution import EvaluationTest
from app.schemas.test_execution import (
    EvaluationTestRead,
    TestAttemptCreate,
    TestAttemptRead,
    TestStepRead,
)
from app.services.test_service import create_retest_attempt, get_evaluation_test

router = APIRouter(tags=["Evaluation Tests"])


@router.get("/evaluation-tests/{test_id}", response_model=EvaluationTestRead)
def get_test_details(
    test_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> EvaluationTestRead:
    """Retrieve details of an instantiated evaluation test, including all attempts and steps."""
    t = get_evaluation_test(db, test_id)
    if not t:
        raise HTTPException(status_code=404, detail="Evaluation test not found")

    attempts_data = []
    for att in t.attempts:
        steps_data = [
            TestStepRead.model_validate(step) for step in att.steps
        ]
        attempts_data.append(
            TestAttemptRead(
                id=att.id,
                evaluation_test_id=att.evaluation_test_id,
                attempt_number=att.attempt_number,
                status=att.status,
                started_at=att.started_at,
                completed_at=att.completed_at,
                supersedes_attempt_id=att.supersedes_attempt_id,
                notes=att.notes,
                steps=steps_data,
            )
        )

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
        attempts=attempts_data,
    )


@router.post(
    "/evaluation-tests/{test_id}/attempts",
    response_model=TestAttemptRead,
    status_code=status.HTTP_201_CREATED,
)
def create_retest(
    test_id: uuid.UUID,
    payload: TestAttemptCreate,
    db: Session = Depends(get_db),
) -> TestAttemptRead:
    """Create a new retest attempt (Attempt N+1) preserving previous attempt history without mutation."""
    try:
        new_attempt = create_retest_attempt(db, test_id, notes=payload.notes)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    steps_data = [TestStepRead.model_validate(s) for s in new_attempt.steps]
    return TestAttemptRead(
        id=new_attempt.id,
        evaluation_test_id=new_attempt.evaluation_test_id,
        attempt_number=new_attempt.attempt_number,
        status=new_attempt.status,
        started_at=new_attempt.started_at,
        completed_at=new_attempt.completed_at,
        supersedes_attempt_id=new_attempt.supersedes_attempt_id,
        notes=new_attempt.notes,
        steps=steps_data,
    )
