import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models import Employee
from app.repositories import DepartmentRepository, EmployeeRepository
from app.schemas.employee import EmployeeCreate, EmployeeRead

logger = logging.getLogger(__name__)


class EmployeeService:
    MAX_FIELD_LENGTH = 200

    def __init__(
        self,
        session: AsyncSession,
        dept_repo: DepartmentRepository,
        emp_repo: EmployeeRepository,
    ):
        self.session = session
        self.dept_repo = dept_repo
        self.emp_repo = emp_repo

    async def create_employee(
        self,
        department_id: int,
        data: EmployeeCreate,
    ) -> EmployeeRead:
        if not await self.dept_repo.exists(department_id):
            raise NotFoundError(f"Department {department_id} not found")
        
        full_name = data.full_name.strip()
        position = data.position.strip()
        
        if not full_name or not position:
            raise ValidationError("full_name and position cannot be empty after trimming")
        
        employee = await self.emp_repo.create(
            department_id=department_id,
            full_name=full_name,
            position=position,
            hired_at=data.hired_at,
        )
        await self.session.commit()
        await self.session.refresh(employee)
        
        return EmployeeRead.model_validate(employee)