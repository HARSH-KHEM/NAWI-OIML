"""Pydantic schemas for test execution entities."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.models.test_execution import EvaluationTestStatus, TestAttemptStatus, TestStepStatus


class TestStepRead(BaseModel):
    """Schema for test steps."""
    id: uuid.UUID
    test_attempt_id: uuid.UUID
    step_code: str
    sequence: int
    title: str
    instruction: str
    status: TestStepStatus
    required: bool
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ObservationCreate(BaseModel):
    """Payload to record a raw laboratory observation."""
    observation_code: str = Field(..., min_length=1, max_length=64)
    value_numeric: Optional[Decimal] = None
    value_text: Optional[str] = None
    unit: Optional[str] = Field(default=None, max_length=16)
    value_json: Optional[Dict[str, Any]] = None
    test_step_id: Optional[uuid.UUID] = None
    entered_by: Optional[str] = None
    notes: Optional[str] = None


class ObservationUpdate(BaseModel):
    """Payload to update an observation."""
    value_numeric: Optional[Decimal] = None
    value_text: Optional[str] = None
    notes: Optional[str] = None


class ObservationRead(BaseModel):
    """Schema for reading an observation."""
    id: uuid.UUID
    test_attempt_id: uuid.UUID
    test_step_id: Optional[uuid.UUID] = None
    observation_code: str
    value_numeric: Optional[Decimal] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    value_json: Optional[Dict[str, Any]] = None
    observed_at: datetime
    entered_by: Optional[str] = None
    validation_status: str
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TestAttemptCreate(BaseModel):
    """Payload to create a retest attempt."""
    notes: Optional[str] = None


class TestAttemptRead(BaseModel):
    """Schema for test attempts."""
    id: uuid.UUID
    evaluation_test_id: uuid.UUID
    attempt_number: int
    status: TestAttemptStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    supersedes_attempt_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    steps: List[TestStepRead] = Field(default_factory=list)
    observations: List[ObservationRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class EvaluationTestRead(BaseModel):
    """Schema for instantiated evaluation tests."""
    id: uuid.UUID
    evaluation_id: uuid.UUID
    test_definition_id: uuid.UUID
    rule_version_id: uuid.UUID
    sequence: int
    status: EvaluationTestStatus
    scope_type: str
    range_reference: Optional[str] = None
    range_index: Optional[int] = None
    applicability_reason: str
    implementation_status: str
    test_code: Optional[str] = None
    title: Optional[str] = None
    r76_reference: Optional[str] = None
    attempts: List[TestAttemptRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


from enum import Enum


class RepeatabilitySeries(str, Enum):
    SERIES_50 = "50_PERCENT_MAX"
    SERIES_100 = "100_PERCENT_MAX"


class RepeatabilityObservationPayload(BaseModel):
    """Strict payload for repeatability observation in value_json."""
    series: RepeatabilitySeries
    weighing_index: int = Field(..., gt=0, description="Positive 1-based weighing index within series")
    test_load: Decimal = Field(..., gt=0, description="Exact test load applied")
    loaded_indication: Decimal = Field(..., description="Observed indication under load")
    unloaded_indication: Decimal = Field(..., description="Observed rested indication after unloading")
    unit: Optional[str] = Field(default=None, max_length=16)

    model_config = ConfigDict(extra="forbid")


class EccentricityObservationPayload(BaseModel):
    """Payload for eccentricity observation in value_json."""
    position: str = Field(
        ...,
        min_length=2,
        max_length=64,
        pattern=r"^[A-Z0-9_]+$",
        description="Procedure-agnostic position identifier (e.g. QUARTER_1, SUPPORT_1, ROLL_BEGIN)",
    )
    load: Optional[Decimal] = Field(default=None, gt=0, description="Applied test load")
    indication: Optional[Decimal] = Field(default=None, description="Indication at specified position")
    additional_load: Optional[Decimal] = Field(default=None, description="Additional load to find changeover point (ΔL)")
    zero_error: Optional[Decimal] = Field(default=None, description="Zero error E0 prior to loading")
    unit: Optional[str] = Field(default=None, max_length=16)

    model_config = ConfigDict(extra="forbid")

