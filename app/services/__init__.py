from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories import DepartmentRepository, EmployeeRepository
from .department import DepartmentService
from .employee import EmployeeService


def get_department_service(
    session: AsyncSession = Depends(get_session),
) -> DepartmentService:
    return DepartmentService(
        session=session,
        dept_repo=DepartmentRepository(session),
        emp_repo=EmployeeRepository(session),
    )


def get_employee_service(
    session: AsyncSession = Depends(get_session),
) -> EmployeeService:
    return EmployeeService(
        session=session,
        dept_repo=DepartmentRepository(session),
        emp_repo=EmployeeRepository(session),
    )


__all__ = [
    "DepartmentService",
    "EmployeeService", 
    "get_department_service",
    "get_employee_service",
]