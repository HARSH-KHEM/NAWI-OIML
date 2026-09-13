"""Instrument Pydantic schemas."""

from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.models.instrument import InstrumentStatus


class InstrumentBase(BaseModel):
    """Base fields for an Instrument."""
    manufacturer: str = Field(..., min_length=1, max_length=255)
    model_name: str = Field(..., min_length=1, max_length=255)
    instrument_family: str = Field(default="NAWI", max_length=100)
    serial_number: str = Field(..., min_length=1, max_length=100)
    status: InstrumentStatus = InstrumentStatus.DRAFT
    is_synthetic: bool = Field(
        default=False,
        description="Must be True for synthetic demo data; False for real instruments",
    )


class InstrumentCreate(InstrumentBase):
    """Schema for instrument creation."""
    pass


class InstrumentRead(InstrumentBase):
    """Schema for reading an instrument."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
