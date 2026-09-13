"""Pydantic schemas for canonical test definitions."""

import uuid
from pydantic import BaseModel, ConfigDict
from app.models.test_definition import ImplementationStatus, ScopeType


class TestDefinitionRead(BaseModel):
    """Schema for reading a test definition."""
    id: uuid.UUID
    test_code: str
    title: str
    r76_reference: str
    description: str | None = None
    implementation_status: ImplementationStatus
    scope_type: ScopeType
    sequence: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
