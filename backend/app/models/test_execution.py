"""SQLAlchemy models for test execution: EvaluationTest, TestAttempt, TestStep, and Observation."""

from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import enum
import uuid
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CommonBaseModel

if TYPE_CHECKING:
    from app.models.evaluation import Evaluation
    from app.models.metrology import Calculation, ComplianceResult
    from app.models.rule import RuleVersion
    from app.models.test_definition import TestDefinition


class EvaluationTestStatus(str, enum.Enum):
    """Lifecycle status of an instantiated evaluation test."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    INCOMPLETE = "INCOMPLETE"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TestAttemptStatus(str, enum.Enum):
    """Lifecycle status of an execution attempt."""
    __test__ = False
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    SUPERSEDED = "SUPERSEDED"
    ABANDONED = "ABANDONED"


class TestStepStatus(str, enum.Enum):
    """Execution status of a procedural test step."""
    __test__ = False
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"


class EvaluationTest(CommonBaseModel):
    """An instantiated test procedure within a generated evaluation plan.
    
    Preserves rule_version_id and range context independently.
    """

    __tablename__ = "evaluation_tests"

    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_definition_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_definitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    rule_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("rule_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    status: Mapped[EvaluationTestStatus] = mapped_column(
        Enum(EvaluationTestStatus, name="evaluation_test_status_enum", native_enum=False),
        default=EvaluationTestStatus.NOT_STARTED,
        nullable=False,
        index=True,
    )
    scope_type: Mapped[str] = mapped_column(
        String(32),
        default="INSTRUMENT",
        nullable=False,
    )
    range_reference: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="e.g. RANGE_1, RANGE_2 for multiple range instruments",
    )
    range_index: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    applicability_reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Detailed rationale explaining why this test is or is not applicable",
    )
    implementation_status: Mapped[str] = mapped_column(
        String(64),
        default="IMPLEMENTED",
        nullable=False,
    )

    # Relationships
    evaluation: Mapped["Evaluation"] = relationship(
        "Evaluation",
        back_populates="tests",
    )
    test_definition: Mapped["TestDefinition"] = relationship(
        "TestDefinition",
        back_populates="evaluation_tests",
    )
    rule_version: Mapped["RuleVersion"] = relationship(
        "RuleVersion",
    )
    attempts: Mapped[List["TestAttempt"]] = relationship(
        "TestAttempt",
        back_populates="evaluation_test",
        cascade="all, delete-orphan",
        order_by="TestAttempt.attempt_number",
    )

    def __repr__(self) -> str:
        return (
            f"<EvaluationTest id={self.id} eval={self.evaluation_id} "
            f"test_def={self.test_definition_id} status={self.status}>"
        )


class TestAttempt(CommonBaseModel):
    """An execution attempt for an EvaluationTest.
    
    Retesting generates a new TestAttempt row (e.g. Attempt 2).
    Attempt 1 remains immutable in the audit history.
    """

    __tablename__ = "test_attempts"
    __test__ = False

    evaluation_test_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evaluation_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    status: Mapped[TestAttemptStatus] = mapped_column(
        Enum(TestAttemptStatus, name="test_attempt_status_enum", native_enum=False),
        default=TestAttemptStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    supersedes_attempt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_attempts.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    evaluation_test: Mapped["EvaluationTest"] = relationship(
        "EvaluationTest",
        back_populates="attempts",
    )
    steps: Mapped[List["TestStep"]] = relationship(
        "TestStep",
        back_populates="test_attempt",
        cascade="all, delete-orphan",
        order_by="TestStep.sequence",
    )
    observations: Mapped[List["Observation"]] = relationship(
        "Observation",
        back_populates="test_attempt",
        cascade="all, delete-orphan",
        order_by="Observation.created_at",
    )
    calculations: Mapped[List["Calculation"]] = relationship(
        "Calculation",
        back_populates="test_attempt",
        cascade="all, delete-orphan",
        order_by="Calculation.calculated_at",
    )
    compliance_results: Mapped[List["ComplianceResult"]] = relationship(
        "ComplianceResult",
        back_populates="test_attempt",
        cascade="all, delete-orphan",
        order_by="ComplianceResult.decided_at",
    )

    def __repr__(self) -> str:
        return (
            f"<TestAttempt id={self.id} test={self.evaluation_test_id} "
            f"attempt={self.attempt_number} status={self.status}>"
        )


class TestStep(CommonBaseModel):
    """An individual procedural step inside a test attempt."""

    __tablename__ = "test_steps"
    __test__ = False

    test_attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Identifier for step, e.g. STEP_ZERO_ERROR, STEP_LOAD_POINT_1",
    )
    sequence: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    instruction: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    status: Mapped[TestStepStatus] = mapped_column(
        Enum(TestStepStatus, name="test_step_status_enum", native_enum=False),
        default=TestStepStatus.PENDING,
        nullable=False,
    )
    required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # Relationships
    test_attempt: Mapped["TestAttempt"] = relationship(
        "TestAttempt",
        back_populates="steps",
    )
    observations: Mapped[List["Observation"]] = relationship(
        "Observation",
        back_populates="test_step",
    )

    def __repr__(self) -> str:
        return f"<TestStep id={self.id} code={self.step_code!r} seq={self.sequence}>"


class Observation(CommonBaseModel):
    """Raw metrological laboratory measurement captured during testing.
    
    Stores exact numeric inputs using PostgreSQL NUMERIC(20, 6) / Python Decimal.
    """

    __tablename__ = "observations"

    test_attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_step_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_steps.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    observation_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Observation quantity code, e.g. LOAD, INDICATION, ADDITIONAL_LOAD, ZERO_ERROR, POSITION",
    )
    value_numeric: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=20, scale=6, asdecimal=True),
        nullable=True,
        comment="Exact decimal value for metrological calculations",
    )
    value_text: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    unit: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
        comment="e.g. kg, g, mg, °C",
    )
    value_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    entered_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    validation_status: Mapped[str] = mapped_column(
        String(32),
        default="VALID",
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    test_attempt: Mapped["TestAttempt"] = relationship(
        "TestAttempt",
        back_populates="observations",
    )
    test_step: Mapped[Optional["TestStep"]] = relationship(
        "TestStep",
        back_populates="observations",
    )

    def __repr__(self) -> str:
        return (
            f"<Observation id={self.id} code={self.observation_code!r} "
            f"val={self.value_numeric} {self.unit}>"
        )
