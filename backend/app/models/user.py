"""User SQLAlchemy model."""

from typing import TYPE_CHECKING, List
import enum
from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CommonBaseModel

if TYPE_CHECKING:
    from app.models.evaluation import Evaluation


class UserRole(str, enum.Enum):
    """User operational roles in the laboratory."""
    OPERATOR = "OPERATOR"
    LAB_ADMIN = "LAB_ADMIN"
    AUDITOR = "AUDITOR"


class User(CommonBaseModel):
    """User account entity."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", native_enum=False),
        default=UserRole.OPERATOR,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="operator",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
