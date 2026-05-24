"""ORM models.

Importing this package imports every model module, which registers all
tables on `Base.metadata` (used by Alembic for autogeneration).
"""

from app.models.department import Department
from app.models.employee import Employee

__all__ = ["Department", "Employee"]
