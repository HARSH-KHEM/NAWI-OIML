"""Health check schema."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for health status endpoint."""
    status: str = Field(default="ok", description="Application operational status")
    app: str = Field(..., description="Application name")
    version: str = Field(..., description="Current application version")
    environment: str = Field(..., description="Active runtime environment")
    database_connected: bool = Field(..., description="True if PostgreSQL is reachable")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response generation UTC timestamp",
    )
