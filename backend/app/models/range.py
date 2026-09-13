"""Instrument Configuration Range SQLAlchemy model for multi-range NAWI instruments."""

from decimal import Decimal
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CommonBaseModel

if TYPE_CHECKING:
    from app.models.configuration import InstrumentConfiguration


class InstrumentConfigurationRange(CommonBaseModel):
    """Represents an individual weighing range of a multiple-range or multi-interval instrument.
    
    Ref: OIML R 76-1:2006, T.3.2.2 & 3.2.3.
    Each range (i = 1, 2, ...) has independent Max_i, Min_i, e_i, d_i.
    """

    __tablename__ = "instrument_configuration_ranges"

    configuration_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("instrument_configurations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    range_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="1-based index of the weighing range (e.g., 1 for Range 1, 2 for Range 2)",
    )

    max_capacity: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=6, asdecimal=True),
        nullable=False,
        comment="Maximum capacity of this range (Max_i)",
    )
    min_capacity: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=6, asdecimal=True),
        nullable=False,
        comment="Minimum capacity of this range (Min_i)",
    )
    verification_scale_interval: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=6, asdecimal=True),
        nullable=False,
        comment="Verification scale interval of this range (e_i)",
    )
    actual_scale_interval: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=6, asdecimal=True),
        nullable=False,
        comment="Actual scale interval of this range (d_i)",
    )

    unit: Mapped[str] = mapped_column(
        String(16),
        default="kg",
        nullable=False,
    )

    # Relationships
    configuration: Mapped["InstrumentConfiguration"] = relationship(
        "InstrumentConfiguration",
        back_populates="ranges",
    )

    __table_args__ = (
        CheckConstraint("range_index >= 1", name="check_range_index_gte_1"),
        CheckConstraint("min_capacity > 0", name="check_range_min_capacity_positive"),
        CheckConstraint("max_capacity > 0", name="check_range_max_capacity_positive"),
        CheckConstraint("min_capacity <= max_capacity", name="check_range_min_lte_max"),
        CheckConstraint(
            "actual_scale_interval <= verification_scale_interval",
            name="check_range_d_lte_e",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<InstrumentConfigurationRange id={self.id} range_index={self.range_index} "
            f"Max={self.max_capacity}{self.unit} e={self.verification_scale_interval}{self.unit}>"
        )
