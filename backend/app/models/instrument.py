"""Instrument SQLAlchemy model."""

from typing import TYPE_CHECKING, List
import enum
from sqlalchemy import Boolean, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CommonBaseModel

if TYPE_CHECKING:
    from app.models.configuration import InstrumentConfiguration
    from app.models.evaluation import Evaluation


class InstrumentStatus(str, enum.Enum):
    """Instrument lifecycle status."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Instrument(CommonBaseModel):
    """Persistent physical/type identity of a weighing instrument under evaluation.
    
    Does NOT store mutable historical evaluation state.
    """

    __tablename__ = "instruments"

    manufacturer: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    instrument_family: Mapped[str] = mapped_column(
        String(100),
        default="NAWI",
        nullable=False,
        comment="Instrument family, e.g. NAWI (Non-Automatic Weighing Instrument)",
    )
    serial_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    status: Mapped[InstrumentStatus] = mapped_column(
        Enum(InstrumentStatus, name="instrument_status_enum", native_enum=False),
        default=InstrumentStatus.DRAFT,
        nullable=False,
    )
    is_synthetic: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Flag indicating synthetic demo/test instrument; never an approved instrument",
    )

    # Relationships
    configurations: Mapped[List["InstrumentConfiguration"]] = relationship(
        "InstrumentConfiguration",
        back_populates="instrument",
        cascade="all, delete-orphan",
        order_by="desc(InstrumentConfiguration.created_at)",
    )
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="instrument",
    )

    __table_args__ = (
        Index("ix_instruments_manufacturer_model", "manufacturer", "model_name"),
    )

    def __repr__(self) -> str:
        return (
            f"<Instrument id={self.id} manufacturer={self.manufacturer!r} "
            f"model={self.model_name!r} serial={self.serial_number!r}>"
        )
