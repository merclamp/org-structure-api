from sqlalchemy import select, update

from app.models import Department
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository):
    async def get(self, department_id: int) -> Department | None:
        return await self.session.get(Department, department_id)

    async def exists(self, department_id: int) -> bool:
        """Return whether a department with the given id exists."""
        result = await self.session.execute(
            select(Department.id)
            .where(Department.id == department_id)
            .limit(1)
        )
        return result.first() is not None

    async def name_exists_in_parent(
        self,
        name: str,
        parent_id: int | None,
        *,
        exclude_id: int | None = None,
    ) -> bool:
        stmt = select(Department.id).where(
            Department.name == name,
            Department.parent_id.is_not_distinct_from(parent_id),
        )
        if exclude_id is not None:
            stmt = stmt.where(Department.id != exclude_id)
        result = await self.session.execute(stmt.limit(1))
        return result.first() is not None

    async def create(
        self,
        *,
        name: str,
        parent_id: int | None,
    ) -> Department:
        department = Department(name=name, parent_id=parent_id)
        self.session.add(department)
        await self.session.flush()
        return department

    async def get_subtree(
        self,
        root: Department,
        max_depth: int,
    ) -> list[Department]:
        collected: list[Department] = [root]
        frontier: list[int] = [root.id]

        for _ in range(max_depth):
            if not frontier:
                break
            result = await self.session.execute(
                select(Department)
                .where(Department.parent_id.in_(frontier))
                .order_by(Department.created_at, Department.id)
            )
            level = list(result.scalars().all())
            if not level:
                break
            collected.extend(level)
            frontier = [department.id for department in level]

        return collected

    async def get_descendant_ids(self, department_id: int) -> set[int]:
        hierarchy = (
            select(Department.id)
            .where(Department.parent_id == department_id)
            .cte(name="subtree", recursive=True)
        )
        hierarchy = hierarchy.union_all(
            select(Department.id).join(
                hierarchy, Department.parent_id == hierarchy.c.id
            )
        )
        result = await self.session.execute(select(hierarchy.c.id))
        return set(result.scalars().all())

    async def reparent_children(
        self,
        department_id: int,
        new_parent_id: int | None,
    ) -> None:
        await self.session.execute(
            update(Department)
            .where(Department.parent_id == department_id)
            .values(parent_id=new_parent_id)
        )

    async def delete(self, department: Department) -> None:
        await self.session.delete(department)
        await self.session.flush()
