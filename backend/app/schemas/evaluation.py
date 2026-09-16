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


class ProcedureReportItem(BaseModel):
    """Report representation of an individual procedure execution."""
    id: str
    test_code: str
    title: str
    r76_reference: str
    status: str
    scope_type: str
    range_reference: Optional[str] = None
    applicability_reason: Optional[str] = None
    implementation_status: str
    attempt_count: int = 0
    latest_decision: Optional[str] = None
    calculated_error: Optional[str] = None
    mpe_limit: Optional[str] = None
    margin: Optional[str] = None


class EvaluationReportResponse(BaseModel):
    """Comprehensive OIML R-76 technical evaluation report."""
    evaluation_id: str
    evaluation_number: str
    status: str
    instrument_id: str
    instrument_manufacturer: str
    instrument_model: str
    instrument_serial: str
    accuracy_class: str
    max_capacity: str
    min_capacity: str
    verification_scale_interval: str
    actual_scale_interval: str
    unit: str
    is_multiple_range: bool
    number_of_ranges: int
    tare_type: str
    standard_name: str
    rule_version: str
    lab_name: Optional[str] = None
    operator_name: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    total_procedures: int
    applicable_procedures: int
    executed_procedures: int
    passed_procedures: int
    failed_procedures: int
    overall_compliance: str
    document_hash: str
    compliance_statement: str
    procedures: List[ProcedureReportItem] = Field(default_factory=list)
    configuration_snapshot: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)
