"""Evaluation Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.models.evaluation import EvaluationStatus
from app.schemas.test_execution import EvaluationTestRead


class EvaluationBase(BaseModel):
    """Base fields for an Evaluation."""
    evaluation_number: str = Field(..., max_length=64)
    instrument_id: uuid.UUID
    instrument_configuration_id: uuid.UUID
    rule_version_id: uuid.UUID
    configuration_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Immutable snapshot of the configuration",
    )
    status: EvaluationStatus = EvaluationStatus.DRAFT
    operator_id: Optional[uuid.UUID] = None
    lab_name: Optional[str] = Field(default=None, max_length=255)
    start_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class EvaluationCreate(BaseModel):
    """Payload to create an Evaluation."""
    evaluation_number: Optional[str] = None
    instrument_configuration_id: Optional[uuid.UUID] = None
    rule_version_id: Optional[uuid.UUID] = None
    lab_name: Optional[str] = "National Metrology Institute"
    operator_id: Optional[uuid.UUID] = None


class EvaluationRead(EvaluationBase):
    """Schema for reading an Evaluation."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationPlanResponse(BaseModel):
    """Response returned when a test plan is generated or retrieved."""
    evaluation_id: uuid.UUID
    evaluation_number: str
    status: EvaluationStatus
    configuration_snapshot: Dict[str, Any]
    tests: List[EvaluationTestRead] = Field(default_factory=list)
    total_tests: int
    applicable_tests_count: int

    model_config = ConfigDict(from_attributes=True)
