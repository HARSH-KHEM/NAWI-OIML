"""Test Definition SQLAlchemy model representing canonical R-76 evaluation procedures."""

from typing import TYPE_CHECKING, List, Optional
import enum
from sqlalchemy import Boolean, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CommonBaseModel

if TYPE_CHECKING:
    from app.models.test_execution import EvaluationTest


class ImplementationStatus(str, enum.Enum):
    """Execution readiness status of a test procedure."""
    IMPLEMENTED = "IMPLEMENTED"                # Full calculation & compliance engine
    PARTIAL = "PARTIAL"                        # Workflow / lightweight calculation
    APPLICABILITY_ONLY = "APPLICABILITY_ONLY"  # Rule applicability evaluated, procedure not automated
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"        # Placeholder without automated workflow


class ScopeType(str, enum.Enum):
    """Scope of execution for an evaluation test."""
    INSTRUMENT = "INSTRUMENT"  # Applies once to the entire instrument
    RANGE = "RANGE"            # Applies separately to each partial weighing range


class TestDefinition(CommonBaseModel):
    """Canonical specification of an OIML R-76 test procedure."""

    __tablename__ = "test_definitions"
    __test__ = False

    test_code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique identifier, e.g. WEIGHING_PERFORMANCE, ECCENTRICITY, REPEATABILITY",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    r76_reference: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Authoritative OIML R 76-1:2006 clause, e.g. A.4.4, A.4.7, A.4.10, A.6",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    implementation_status: Mapped[ImplementationStatus] = mapped_column(
        Enum(ImplementationStatus, name="implementation_status_enum", native_enum=False),
        default=ImplementationStatus.APPLICABILITY_ONLY,
        nullable=False,
    )
    scope_type: Mapped[ScopeType] = mapped_column(
        Enum(ScopeType, name="scope_type_enum", native_enum=False),
        default=ScopeType.INSTRUMENT,
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
        comment="Default recommended sequence in the evaluation plan",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    evaluation_tests: Mapped[List["EvaluationTest"]] = relationship(
        "EvaluationTest",
        back_populates="test_definition",
    )

    def __repr__(self) -> str:
        return (
            f"<TestDefinition id={self.id} code={self.test_code!r} "
            f"ref={self.r76_reference!r} status={self.implementation_status}>"
        )
