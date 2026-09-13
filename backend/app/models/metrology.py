"""SQLAlchemy models for metrology results: Calculation, ComplianceResult, Evidence, and AuditEvent."""

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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CommonBaseModel

if TYPE_CHECKING:
    from app.models.evaluation import Evaluation
    from app.models.rule import RuleVersion
    from app.models.test_execution import Observation, TestAttempt


class ComplianceDecision(str, enum.Enum):
    """Deterministic metrological compliance decisions."""
    PASS = "PASS"
    FAIL = "FAIL"
    INCOMPLETE = "INCOMPLETE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Calculation(CommonBaseModel):
    """Authoritative output of a deterministic metrological calculation.
    
    Preserves exact input snapshot alongside calculated outputs and formula reference.
    """

    __tablename__ = "calculations"

    test_attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    calculation_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="e.g. R76_A4_4_3_ERROR, R76_ECCENTRICITY, R76_REPEATABILITY",
    )
    input_snapshot_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Immutable frozen inputs used to execute the calculation",
    )
    output_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Calculated outputs, e.g. P, E, Ec, MPE, margin",
    )
    formula_reference: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="Exact R-76 clause and formula, e.g. OIML R 76-1:2006, A.4.4.3",
    )
    rule_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("rule_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    test_attempt: Mapped["TestAttempt"] = relationship(
        "TestAttempt",
        back_populates="calculations",
    )
    compliance_results: Mapped[List["ComplianceResult"]] = relationship(
        "ComplianceResult",
        back_populates="calculation",
    )

    def __repr__(self) -> str:
        return (
            f"<Calculation id={self.id} code={self.calculation_code!r} "
            f"ref={self.formula_reference!r}>"
        )


class ComplianceResult(CommonBaseModel):
    """Authoritative compliance decision against OIML R-76 criterion.
    
    Contains structured deterministic reasoning without any AI/LLM.
    """

    __tablename__ = "compliance_results"

    test_attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    calculation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("calculations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    decision: Mapped[ComplianceDecision] = mapped_column(
        Enum(ComplianceDecision, name="compliance_decision_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    criterion_value: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="e.g. <= 0.010 kg (mpe)",
    )
    measured_value: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="e.g. 0.005 kg",
    )
    margin: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="e.g. +0.005 kg (within tolerance) or -0.002 kg (exceeded)",
    )
    rule_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("rule_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    reasoning_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Deterministic explanation: decision, measured, criterion, margin, clause, explanation",
    )
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    test_attempt: Mapped["TestAttempt"] = relationship(
        "TestAttempt",
        back_populates="compliance_results",
    )
    calculation: Mapped[Optional["Calculation"]] = relationship(
        "Calculation",
        back_populates="compliance_results",
    )

    def __repr__(self) -> str:
        return (
            f"<ComplianceResult id={self.id} decision={self.decision} "
            f"measured={self.measured_value!r} criterion={self.criterion_value!r}>"
        )


class Evidence(CommonBaseModel):
    """Artifact metadata linking files, photos, or raw evidence to tests/evaluations."""

    __tablename__ = "evidence"

    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_attempt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_attempts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    observation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("observations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    calculation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("calculations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    evidence_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="e.g. OBSERVATION_RECORD, CALCULATION_SHEET, CALIBRATION_CERT, PHOTO",
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    uploaded_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Evidence id={self.id} type={self.evidence_type!r} file={self.filename!r}>"


class AuditEvent(CommonBaseModel):
    """Immutable audit trail of metrological actions and transitions."""

    __tablename__ = "audit_events"

    evaluation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evaluations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="e.g. EVALUATION, TEST_ATTEMPT, OBSERVATION, CALCULATION, COMPLIANCE",
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="e.g. PLAN_GENERATED, OBSERVATION_RECORDED, CALCULATION_EXECUTED, RETEST_CREATED",
    )
    actor_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    before_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    after_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<AuditEvent id={self.id} action={self.action!r} "
            f"entity={self.entity_type}:{self.entity_id}>"
        )
