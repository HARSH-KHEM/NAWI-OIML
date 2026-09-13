"""Observation management REST API endpoints."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.test_execution import ObservationRead, ObservationUpdate
from app.services.test_service import ObservationLockedError, update_observation

router = APIRouter(tags=["Observations"])


@router.patch("/observations/{observation_id}", response_model=ObservationRead)
def patch_observation(
    observation_id: uuid.UUID,
    payload: ObservationUpdate,
    db: Session = Depends(get_db),
) -> ObservationRead:
    """Modify an existing observation with automatic audit logging."""
    try:
        obs = update_observation(
            db=db,
            observation_id=observation_id,
            value_numeric=payload.value_numeric,
            value_text=payload.value_text,
            notes=payload.notes,
        )
    except ObservationLockedError as exc:
        raise HTTPException(
            status_code=409,
            detail={"error_code": "OBSERVATION_LOCKED", "message": str(exc)},
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return ObservationRead.model_validate(obs)
