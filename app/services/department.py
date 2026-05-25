import logging
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.models import Department, Employee
from app.repositories import DepartmentRepository, EmployeeRepository, department
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentRead,
    DepartmentTree,
)
from app.schemas.employee import EmployeeRead

logger = logging.getLogger(__name__)


class DepartmentService:
    MAX_DEPTH = 5
    MAX_NAME_LENGTH = 200

    def __init__(
        self,
        session: AsyncSession,
        dept_repo: DepartmentRepository,
        emp_repo: EmployeeRepository,
    ):
        self.session = session
        self.dept_repo = dept_repo
        self.emp_repo = emp_repo

    async def create_department(
        self,
        data: DepartmentCreate,
    ) -> DepartmentRead:
        if await self.dept_repo.name_exists_in_parent(
            name=data.name.strip(),
            parent_id=data.parent_id,
        ):
            raise ConflictError(
                f"Department '{data.name}' already exists under this parent"
            )
        
        department = await self.dept_repo.create(
            name=data.name.strip(),
            parent_id=data.parent_id,
        )
        await self.session.commit()
        await self.session.refresh(department)
        
        return DepartmentRead.model_validate(department)

    async def get_department(
        self,
        department_id: int,
        depth: int = 1,
        include_employees: bool = True,
    ) -> dict:
        if not 1 <= depth <= self.MAX_DEPTH:
            raise ValidationError(f"Depth must be between 1 and {self.MAX_DEPTH}")
        
        if not await self.dept_repo.exists(department_id):
            raise NotFoundError(f"Department {department_id} not found")
        
        root = await self.dept_repo.get(department_id)
        assert root is not None

        departments = await self.dept_repo.get_subtree(
            root=root,
            max_depth=depth,
        )
        dept_ids = [d.id for d in departments]
        
        employees_map = {}
        if include_employees:
            employees = await self.emp_repo.list_for_departments(dept_ids)
            employees_map = {
                emp.department_id: 
                [EmployeeRead.model_validate(e) for e in employees 
                 if e.department_id == emp.department_id]
                for emp in employees
            }
        
        dept_map = {d.id: d for d in departments}
        root = dept_map[department_id]
        
        def build_tree(dept: Department) -> DepartmentTree:
            children = [
                build_tree(child)
                for child in dept_map.values()
                if child.parent_id == dept.id
            ]
            return DepartmentTree(
                department=DepartmentRead.model_validate(dept),
                employees=employees_map.get(dept.id, []),
                children=children,
            )
        
        tree = build_tree(root)
        return tree.model_dump()

    async def update_department(
        self,
        department_id: int,
        data: DepartmentUpdate,
    ) -> DepartmentRead:
        department = await self.dept_repo.get(department_id)
        if not department:
            raise NotFoundError(f"Department {department_id} not found")
        
        if data.name is not None:
            name = data.name.strip()
            if await self.dept_repo.name_exists_in_parent(
                name=name,
                parent_id=data.parent_id or department.parent_id,
                exclude_id=department_id,
            ):
                raise ConflictError(
                    f"Department '{name}' already exists under this parent"
                )
            department.name = name
        
        if data.parent_id is not None and data.parent_id != department.parent_id:
            if await self.dept_repo.would_create_cycle(
                department_id=department_id,
                new_parent_id=data.parent_id,
            ):
                raise ConflictError("Cannot create circular dependency in department tree")
            
            if not await self.dept_repo.exists(data.parent_id):
                raise NotFoundError(f"Parent department {data.parent_id} not found")
            
            department.parent_id = data.parent_id
        
        await self.session.commit()
        await self.session.refresh(department)
        return DepartmentRead.model_validate(department)

    async def delete_department(
        self,
        department_id: int,
        mode: str,
        reassign_to_department_id: int | None = None,
    ) -> None:
        if not await self.dept_repo.exists(department_id):
            raise NotFoundError(f"Department {department_id} not found")
        
        if mode == "reassign":
            if not reassign_to_department_id:
                raise ValidationError("reassign_to_department_id is required for mode='reassign'")
            if not await self.dept_repo.exists(reassign_to_department_id):
                raise NotFoundError(f"Target department {reassign_to_department_id} not found")
            
            await self.emp_repo.reassign(
                from_department_id=department_id,
                to_department_id=reassign_to_department_id,
            )
            await self.session.commit()
        
        department = await self.dept_repo.get(department_id)
        if department is None:
            raise NotFoundError(f"Department {department_id} not found")

        await self.dept_repo.delete(department)
        await self.session.commit()