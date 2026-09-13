"""Evidence management REST API endpoints."""

from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.evaluation import Evaluation
from app.models.metrology import Evidence
from app.schemas.metrology import EvidenceRead

router = APIRouter(tags=["Evidence"])


@router.get("/evaluations/{evaluation_id}/evidence", response_model=List[EvidenceRead])
def list_evaluation_evidence(
    evaluation_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[EvidenceRead]:
    """Retrieve all evidence items attached to an evaluation."""
    ev_record = db.get(Evaluation, evaluation_id)
    if not ev_record:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    items = db.scalars(
        select(Evidence).where(Evidence.evaluation_id == evaluation_id)
    ).all()
    return [EvidenceRead.model_validate(i) for i in items]
