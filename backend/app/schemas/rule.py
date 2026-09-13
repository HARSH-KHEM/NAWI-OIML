"""Rule and RuleVersion Pydantic schemas."""

from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class RuleBase(BaseModel):
    """Base fields for a metrological Rule."""
    code: str = Field(..., max_length=64)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None


class RuleCreate(RuleBase):
    """Payload to create a Rule."""
    pass


class RuleRead(RuleBase):
    """Schema for reading a Rule."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RuleVersionBase(BaseModel):
    """Base fields for a RuleVersion."""
    rule_id: uuid.UUID
    version_number: str = Field(..., max_length=64)
    standard_version: str = Field(..., max_length=128)
    clause: str = Field(..., max_length=64)
    calculation_identifier: str = Field(..., max_length=128)
    applicability_identifier: str = Field(..., max_length=128)
    aggregation_strategy: str = Field(default="ALL_POINTS_PASS", max_length=64)
    is_active: bool = True


class RuleVersionCreate(RuleVersionBase):
    """Payload to create a RuleVersion."""
    pass


class RuleVersionRead(RuleVersionBase):
    """Schema for reading a RuleVersion."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
