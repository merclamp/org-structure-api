"""SQLAlchemy declarative base and shared mixins.

All ORM models inherit from `Base`. Alembic imports `Base.metadata`
to autogenerate migrations.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


class TimestampMixin:
    """Adds a database-managed `created_at` column.

    The value is set by PostgreSQL (`server_default=now()`), so it is
    correct even for rows inserted outside the application.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
