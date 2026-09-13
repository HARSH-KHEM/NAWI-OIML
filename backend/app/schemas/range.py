"""Pydantic schemas for instrument configuration ranges."""

from decimal import Decimal
import uuid
from pydantic import BaseModel, ConfigDict, Field


class RangeBase(BaseModel):
    """Base fields for an individual weighing range."""
    range_index: int = Field(..., ge=1, description="1-based range index")
    min_capacity: Decimal = Field(..., gt=0, description="Minimum capacity (Min_i)")
    max_capacity: Decimal = Field(..., gt=0, description="Maximum capacity (Max_i)")
    verification_scale_interval: Decimal = Field(..., gt=0, description="Verification scale interval (e_i)")
    actual_scale_interval: Decimal = Field(..., gt=0, description="Actual scale interval (d_i)")
    unit: str = Field(default="kg", max_length=16)


class RangeCreate(RangeBase):
    """Payload to create a range."""
    pass


class RangeRead(RangeBase):
    """Schema for reading a range."""
    id: uuid.UUID
    configuration_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
