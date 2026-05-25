import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path, status

from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentRead,
    DepartmentTree,
)
from app.schemas.employee import EmployeeCreate, EmployeeRead
from app.services.department import DepartmentService
from app.services.employee import EmployeeService
from app.services import get_department_service, get_employee_service
from app.core.exceptions import (
    BusinessError,
    NotFoundError,
    ConflictError,
    ValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/departments",
    tags=["departments"],
    responses={
        400: {"description": "Validation Error"},
        404: {"description": "Not Found"},
        409: {"description": "Conflict"},
    },
)

DepartmentServiceDep = Annotated[DepartmentService, Depends(get_department_service)]
EmployeeServiceDep = Annotated[EmployeeService, Depends(get_employee_service)]


@router.post(
    "/",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать подразделение",
)
async def create_department(
    service: DepartmentServiceDep,
    data: DepartmentCreate,
) -> DepartmentRead:
    return await service.create_department(data)


@router.get(
    "/{department_id}",
    response_model=DepartmentTree,
    summary="Получить подразделение (дерево + сотрудники)",
)
async def get_department(
    department_id: Annotated[int, Path(title="ID подразделения")],
    service: DepartmentServiceDep,
    depth: Annotated[
        int,
        Query(title="Глубина вложенности", ge=1, le=5),
    ] = 1,
    include_employees: Annotated[
        bool,
        Query(title="Включить сотрудников"),
    ] = True,
) -> DepartmentTree:
    result = await service.get_department(
        department_id=department_id,
        depth=depth,
        include_employees=include_employees,
    )
    return DepartmentTree.model_validate(result)


@router.patch(
    "/{department_id}",
    response_model=DepartmentRead,
    summary="Обновить подразделение",
)
async def update_department(
    department_id: Annotated[int, Path(title="ID подразделения")],
    service: DepartmentServiceDep,
    data: DepartmentUpdate,
) -> DepartmentRead:
    return await service.update_department(department_id, data)


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить подразделение",
)
async def delete_department(
    department_id: Annotated[int, Path(title="ID подразделения")],
    service: DepartmentServiceDep,
    mode: Annotated[
        str,
        Query(pattern="^(cascade|reassign)$"),
    ],
    reassign_to_department_id: Annotated[
        int | None,
        Query(),
    ] = None,
) -> None:
    await service.delete_department(
        department_id=department_id,
        mode=mode,
        reassign_to_department_id=reassign_to_department_id,
    )


@router.post(
    "/{department_id}/employees",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать сотрудника в подразделении",
)
async def create_employee(
    department_id: Annotated[int, Path(title="ID подразделения")],
    service: EmployeeServiceDep,
    data: EmployeeCreate,
) -> EmployeeRead:
    return await service.create_employee(department_id, data)