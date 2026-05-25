"""Data-access layer for the Department aggregate."""

from sqlalchemy import select, update

from app.models import Department
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository):
    """Database queries for departments and the department tree."""

    async def get(self, department_id: int) -> Department | None:
        """Return a department by id, or ``None`` if it does not exist."""
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
        """Return whether a sibling department already uses ``name``.

        Mirrors the ``uq_department_parent_name`` constraint, including
        its ``NULLS NOT DISTINCT`` behaviour: ``is_not_distinct_from``
        treats two ``NULL`` parents as equal, so the check also covers
        root departments. ``exclude_id`` skips a department from the
        check (used when renaming a department in place).
        """
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
        """Insert a new department and return it with its generated id."""
        department = Department(name=name, parent_id=parent_id)
        self.session.add(department)
        # flush() runs the INSERT now (with RETURNING) so that the
        # caller gets a fully-populated object: id and created_at.
        await self.session.flush()
        return department

    async def get_subtree(
        self,
        root: Department,
        max_depth: int,
    ) -> list[Department]:
        """Return ``root`` plus its descendants down to ``max_depth`` levels.

        The result is a flat list (root first, then breadth-first by
        level); the service layer assembles it into a nested structure.

        Loading is done level by level — one query per level. ``max_depth``
        is capped by the API (<= 5), so the number of round-trips is small
        and bounded. For an unbounded walk see ``get_descendant_ids``.
        """
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
        """Return the ids of every department below ``department_id``.

        The department itself is not included. Implemented as a single
        recursive CTE, so it walks an arbitrarily deep subtree without
        N+1 queries — used for cycle detection when re-parenting.
        """
        # Anchor member: the direct children of the department.
        hierarchy = (
            select(Department.id)
            .where(Department.parent_id == department_id)
            .cte(name="subtree", recursive=True)
        )
        # Recursive member: children of departments already in the CTE.
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
        """Move every direct child of a department under a new parent."""
        await self.session.execute(
            update(Department)
            .where(Department.parent_id == department_id)
            .values(parent_id=new_parent_id)
        )

    async def delete(self, department: Department) -> None:
        """Delete a department.

        Child departments and employees are removed by the database via
        ``ON DELETE CASCADE`` (``passive_deletes`` on the relationships).
        """
        await self.session.delete(department)
        await self.session.flush()
