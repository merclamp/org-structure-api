"""Employee ORM model."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.department import Department


class Employee(TimestampMixin, Base):
    """A person working in a department."""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(
        # ON DELETE CASCADE: removing a department removes its employees
        # (used by the `cascade` delete mode).
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str] = mapped_column(String(200), nullable=False)
    hired_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    # --- Relationships ---------------------------------------------------
    department: Mapped[Department] = relationship(
        "Department",
        back_populates="employees",
    )

    def __repr__(self) -> str:
        return (
            f"Employee(id={self.id!r}, full_name={self.full_name!r}, "
            f"department_id={self.department_id!r})"
        )
