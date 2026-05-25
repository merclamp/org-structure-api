"""Repositories: the data-access layer.

Each repository wraps SQLAlchemy queries for one aggregate and keeps raw
database access out of the service and API layers.
"""

from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository

__all__ = ["DepartmentRepository", "EmployeeRepository"]
