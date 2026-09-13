"""Evaluation SQLAlchemy model."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import enum
import uuid
from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CommonBaseModel

if TYPE_CHECKING:
    from app.models.configuration import InstrumentConfiguration
    from app.models.instrument import Instrument
    from app.models.rule import RuleVersion
    from app.models.test_execution import EvaluationTest
    from app.models.user import User


class EvaluationStatus(str, enum.Enum):
    """Lifecycle status of a type evaluation."""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class Evaluation(CommonBaseModel):
    """Represents a single R-76 Type Evaluation workflow session.
    
    Preserves an immutable configuration_snapshot and references a specific
    RuleVersion so that historical evaluations are 100% deterministic and
    reproducible regardless of future configuration modifications.
    """

    __tablename__ = "evaluations"

    evaluation_number: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="Human-readable unique evaluation identifier, e.g. EVAL-2026-00001",
    )

    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("instruments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    instrument_configuration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("instrument_configurations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    rule_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("rule_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Immutable frozen configuration snapshot captured at evaluation start
    configuration_snapshot: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Immutable frozen snapshot of the InstrumentConfiguration at evaluation initialization",
    )

    status: Mapped[EvaluationStatus] = mapped_column(
        Enum(EvaluationStatus, name="evaluation_status_enum", native_enum=False),
        default=EvaluationStatus.DRAFT,
        nullable=False,
        index=True,
    )

    operator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    lab_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Evaluating laboratory or testing authority name",
    )

    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="evaluations",
    )
    instrument_configuration: Mapped["InstrumentConfiguration"] = relationship(
        "InstrumentConfiguration",
        back_populates="evaluations",
    )
    rule_version: Mapped["RuleVersion"] = relationship(
        "RuleVersion",
        back_populates="evaluations",
    )
    operator: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="evaluations",
    )
    tests: Mapped[List["EvaluationTest"]] = relationship(
        "EvaluationTest",
        back_populates="evaluation",
        cascade="all, delete-orphan",
        order_by="EvaluationTest.sequence",
    )

    def __repr__(self) -> str:
        return (
            f"<Evaluation id={self.id} number={self.evaluation_number!r} "
            f"status={self.status} instrument_id={self.instrument_id}>"
        )
