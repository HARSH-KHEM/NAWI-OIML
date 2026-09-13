"""Rule and RuleVersion SQLAlchemy models."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import uuid
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CommonBaseModel

if TYPE_CHECKING:
    from app.models.evaluation import Evaluation


class Rule(CommonBaseModel):
    """Logical rule identity representing an OIML standard or clause."""

    __tablename__ = "rules"

    code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique identifier code, e.g. OIML-R76-2006 or R76-A4.4",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    versions: Mapped[List["RuleVersion"]] = relationship(
        "RuleVersion",
        back_populates="rule",
        cascade="all, delete-orphan",
        order_by="desc(RuleVersion.created_at)",
    )

    def __repr__(self) -> str:
        return f"<Rule id={self.id} code={self.code!r} name={self.name!r}>"


def get_canonical_rule_definition() -> dict:
    """Canonical structured JSON definition for standard OIML R-76 tests."""
    return {
        "standard": "OIML R 76-1: 2006 (E)",
        "version": "2006-01",
        "tests": {
            "WEIGHING_PERFORMANCE": {
                "clause": "A.4.4.3",
                "calculation_identifier": "R76_A4_4_3_ERROR",
                "criterion": {"type": "ABS_LE_MPE"},
                "mpe": {"source": "TABLE_6"},
            },
            "ECCENTRICITY": {
                "clause": "A.4.7",
                "calculation_identifier": "R76_ECCENTRICITY",
                "criterion": {"type": "MAX_POS_ABS_LE_MPE"},
                "mpe": {"source": "TABLE_6"},
            },
            "REPEATABILITY": {
                "clause": "A.4.10",
                "calculation_identifier": "R76_REPEATABILITY",
                "criterion": {"type": "SPAN_LE_MPE"},
                "mpe": {"source": "TABLE_6"},
            },
        },
    }


class RuleVersion(CommonBaseModel):
    """Specific executable version of a rule.
    
    Evaluations link to a specific RuleVersion to maintain reproducible,
    immutable compliance criteria over time.
    """

    __tablename__ = "rule_versions"

    rule_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Version tag, e.g. 2006-01 or 1.0.0",
    )
    standard_version: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="Official standard publication string, e.g. OIML R 76-1: 2006 (E)",
    )
    clause: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Specific standard clause, e.g. A.4.4, Annex A",
    )
    calculation_identifier: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="Symbolic identifier for the deterministic calculation procedure",
    )
    applicability_identifier: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="Symbolic identifier for the applicability rule routine",
    )
    aggregation_strategy: Mapped[str] = mapped_column(
        String(64),
        default="ALL_POINTS_PASS",
        nullable=False,
        comment="Aggregation strategy for multi-point tests, e.g. ALL_POINTS_PASS",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    definition_json: Mapped[dict] = mapped_column(
        JSON,
        default=get_canonical_rule_definition,
        nullable=False,
        comment="Canonical structured JSON definition of rules and criteria",
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of canonicalized rule definition for tamper evidence",
    )
    effective_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    rule: Mapped["Rule"] = relationship(
        "Rule",
        back_populates="versions",
    )
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="rule_version",
    )

    __table_args__ = (
        UniqueConstraint("rule_id", "version_number", name="uq_rule_versions_rule_version"),
    )

    def __repr__(self) -> str:
        return (
            f"<RuleVersion id={self.id} rule_id={self.rule_id} "
            f"version={self.version_number!r} clause={self.clause!r}>"
        )
