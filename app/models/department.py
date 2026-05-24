"""Department ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class Department(TimestampMixin, Base):
    """An organizational unit.

    Departments form a tree: `parent_id` references another department,
    or is ``NULL`` for a root unit.
    """

    __tablename__ = "departments"
    __table_args__ = (
        # Sibling departments must have unique names. `NULLS NOT DISTINCT`
        # extends the rule to root departments, where parent_id IS NULL
        # (PostgreSQL treats NULLs as equal for this constraint).
        UniqueConstraint(
            "parent_id",
            "name",
            name="uq_department_parent_name",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        # ON DELETE CASCADE lets PostgreSQL recursively remove a whole
        # subtree in a single statement (used by the `cascade` delete mode).
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=True,
    )

    # --- Relationships ---------------------------------------------------
    parent: Mapped[Department | None] = relationship(
        "Department",
        remote_side="Department.id",
        back_populates="children",
    )
    children: Mapped[list[Department]] = relationship(
        "Department",
        back_populates="parent",
        # passive_deletes lets the DB-level cascade do the work instead of
        # SQLAlchemy loading and deleting every child in Python.
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    employees: Mapped[list[Employee]] = relationship(
        "Employee",
        back_populates="department",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f"Department(id={self.id!r}, name={self.name!r}, "
            f"parent_id={self.parent_id!r})"
        )
