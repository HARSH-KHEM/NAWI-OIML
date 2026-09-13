"""Instrument Configuration SQLAlchemy model."""

from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import enum
import uuid
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CommonBaseModel

if TYPE_CHECKING:
    from app.models.evaluation import Evaluation
    from app.models.instrument import Instrument
    from app.models.range import InstrumentConfigurationRange


class AccuracyClass(str, enum.Enum):
    """OIML R-76 Accuracy Classes."""
    CLASS_I = "CLASS_I"        # Special Accuracy
    CLASS_II = "CLASS_II"      # High Accuracy
    CLASS_III = "CLASS_III"    # Medium Accuracy
    CLASS_IIII = "CLASS_IIII"  # Ordinary Accuracy


class TareType(str, enum.Enum):
    """Supported tare mechanism types."""
    SUBTRACTIVE = "SUBTRACTIVE"
    ADDITIVE = "ADDITIVE"
    BOTH = "BOTH"
    NONE = "NONE"


class InstrumentConfiguration(CommonBaseModel):
    """Metrological configuration of an instrument.
    
    All metrological quantities use Decimal / NUMERIC(20, 6)
    to strictly prevent floating-point representation errors.
    """

    __tablename__ = "instrument_configurations"

    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    accuracy_class: Mapped[AccuracyClass] = mapped_column(
        Enum(AccuracyClass, name="accuracy_class_enum", native_enum=False),
        nullable=False,
    )

    # Metrological quantities: NUMERIC(20, 6) mapped to Python Decimal
    max_capacity: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=6, asdecimal=True),
        nullable=False,
        comment="Maximum capacity (Max)",
    )
    min_capacity: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=6, asdecimal=True),
        nullable=False,
        comment="Minimum capacity (Min)",
    )
    verification_scale_interval: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=6, asdecimal=True),
        nullable=False,
        comment="Verification scale interval (e)",
    )
    actual_scale_interval: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=6, asdecimal=True),
        nullable=False,
        comment="Actual scale interval (d)",
    )

    unit: Mapped[str] = mapped_column(
        String(16),
        default="kg",
        nullable=False,
        comment="Metrological unit of measurement, e.g. kg, g, mg",
    )

    # Multi-range parameters
    number_of_ranges: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    is_multiple_range: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Functional capabilities
    tare_type: Mapped[TareType] = mapped_column(
        Enum(TareType, name="tare_type_enum", native_enum=False),
        default=TareType.SUBTRACTIVE,
        nullable=False,
    )
    is_electronic: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    has_zero_setting: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Controlled JSON for non-critical auxiliary properties
    extra_capabilities: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="Auxiliary capability flags/metadata without replacing relational columns",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="configurations",
    )
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="instrument_configuration",
    )
    ranges: Mapped[List["InstrumentConfigurationRange"]] = relationship(
        "InstrumentConfigurationRange",
        back_populates="configuration",
        cascade="all, delete-orphan",
        order_by="InstrumentConfigurationRange.range_index",
    )

    __table_args__ = (
        CheckConstraint("min_capacity > 0", name="check_min_capacity_positive"),
        CheckConstraint("max_capacity > 0", name="check_max_capacity_positive"),
        CheckConstraint("min_capacity <= max_capacity", name="check_min_lte_max"),
        CheckConstraint(
            "actual_scale_interval <= verification_scale_interval",
            name="check_d_lte_e",
        ),
        CheckConstraint("number_of_ranges >= 1", name="check_number_of_ranges_gte_1"),
    )

    def __repr__(self) -> str:
        return (
            f"<InstrumentConfiguration id={self.id} class={self.accuracy_class} "
            f"Max={self.max_capacity}{self.unit} e={self.verification_scale_interval}{self.unit}>"
        )
