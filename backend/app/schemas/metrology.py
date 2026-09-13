"""Pydantic schemas for calculation, compliance, and evidence trace."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.models.metrology import ComplianceDecision


class CalculationRead(BaseModel):
    """Schema for calculation records."""
    id: uuid.UUID
    test_attempt_id: uuid.UUID
    calculation_code: str
    formula_reference: str
    input_snapshot_json: Dict[str, Any]
    output_json: Dict[str, Any]
    rule_version_id: uuid.UUID
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplianceResultRead(BaseModel):
    """Schema for compliance decisions."""
    id: uuid.UUID
    test_attempt_id: uuid.UUID
    calculation_id: Optional[uuid.UUID] = None
    decision: ComplianceDecision
    criterion_value: str
    measured_value: str
    margin: Optional[str] = None
    rule_version_id: uuid.UUID
    reasoning_json: Dict[str, Any]
    decided_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceCreate(BaseModel):
    """Payload to upload/record evidence."""
    evidence_type: str = Field(..., max_length=64)
    filename: str = Field(..., max_length=255)
    storage_key: str = Field(..., max_length=500)
    sha256: str = Field(..., max_length=64)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    uploaded_by: Optional[str] = None


class EvidenceRead(BaseModel):
    """Schema for evidence records."""
    id: uuid.UUID
    evaluation_id: uuid.UUID
    test_attempt_id: Optional[uuid.UUID] = None
    observation_id: Optional[uuid.UUID] = None
    calculation_id: Optional[uuid.UUID] = None
    evidence_type: str
    filename: str
    storage_key: str
    sha256: str
    metadata_json: Dict[str, Any]
    uploaded_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
