"""Data-access layer for the Employee aggregate."""

from collections.abc import Sequence
from datetime import date

from sqlalchemy import select, update

from app.models import Employee
from app.repositories.base import BaseRepository


class EmployeeRepository(BaseRepository):
    async def create(
        self,
        *,
        department_id: int,
        full_name: str,
        position: str,
        hired_at: date | None,
    ) -> Employee:
        employee = Employee(
            department_id=department_id,
            full_name=full_name,
            position=position,
            hired_at=hired_at,
        )
        self.session.add(employee)
        await self.session.flush()
        return employee

    async def list_for_departments(
        self,
        department_ids: Sequence[int],
    ) -> list[Employee]:
        if not department_ids:
            return []
        result = await self.session.execute(
            select(Employee)
            .where(Employee.department_id.in_(department_ids))
            .order_by(Employee.created_at, Employee.id)
        )
        return list(result.scalars().all())

    async def reassign(
        self,
        from_department_id: int,
        to_department_id: int,
    ) -> int:
        result = await self.session.execute(
            update(Employee)
            .where(Employee.department_id == from_department_id)
            .values(department_id=to_department_id)
        )
        return result.rowcount  # type: ignore[attr-defined]
