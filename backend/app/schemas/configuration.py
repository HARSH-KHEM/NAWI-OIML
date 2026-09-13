"""Instrument Configuration Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.configuration import AccuracyClass, TareType


class InstrumentConfigurationBase(BaseModel):
    """Base fields for Instrument Configuration with Decimal precision."""
    accuracy_class: AccuracyClass
    max_capacity: Decimal = Field(..., gt=0, description="Maximum weighing capacity (Max)")
    min_capacity: Decimal = Field(..., gt=0, description="Minimum weighing capacity (Min)")
    verification_scale_interval: Decimal = Field(
        ..., gt=0, description="Verification scale interval (e)"
    )
    actual_scale_interval: Decimal = Field(
        ..., gt=0, description="Actual scale interval (d)"
    )
    unit: str = Field(default="kg", max_length=16)
    number_of_ranges: int = Field(default=1, ge=1)
    is_multiple_range: bool = False
    tare_type: TareType = TareType.SUBTRACTIVE
    is_electronic: bool = True
    has_zero_setting: bool = True
    extra_capabilities: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_metrological_hierarchy(self) -> "InstrumentConfigurationBase":
        """Validate fundamental physical rules."""
        if self.min_capacity > self.max_capacity:
            raise ValueError("min_capacity (Min) cannot exceed max_capacity (Max)")
        if self.actual_scale_interval > self.verification_scale_interval:
            raise ValueError(
                "actual_scale_interval (d) cannot exceed verification_scale_interval (e)"
            )
        return self


from app.schemas.range import RangeCreate, RangeRead


class InstrumentConfigurationCreate(InstrumentConfigurationBase):
    """Payload to create an instrument configuration."""
    instrument_id: Optional[uuid.UUID] = None
    ranges: List[RangeCreate] = Field(default_factory=list)


class InstrumentConfigurationRead(InstrumentConfigurationBase):
    """Schema for reading instrument configuration."""
    id: uuid.UUID
    instrument_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    ranges: List[RangeRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
