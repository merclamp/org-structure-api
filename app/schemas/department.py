"""Pydantic schemas for the Department resource."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.employee import EmployeeRead


class DepartmentBase(BaseModel):
    """Fields shared by department input and output schemas."""

    # See EmployeeBase: trims whitespace so blank names are rejected.
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)


class DepartmentCreate(DepartmentBase):
    """Request body for `POST /departments/`."""

    parent_id: int | None = None


class DepartmentUpdate(BaseModel):
    """Request body for `PATCH /departments/{id}`.

    Both fields are optional. The route applies only the fields the
    client actually sent (``model_dump(exclude_unset=True)``), which is
    what distinguishes an omitted `parent_id` ("leave unchanged") from an
    explicit ``null`` ("move to the tree root").
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = None


class DepartmentRead(DepartmentBase):
    """Department representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int | None
    created_at: datetime


class DepartmentTree(BaseModel):
    """Recursive response for `GET /departments/{id}`.

    `children` holds nested departments up to the requested `depth`;
    `employees` holds the department's own staff (empty when the request
    sets ``include_employees=false``).
    """

    department: DepartmentRead
    employees: list[EmployeeRead] = Field(default_factory=list)
    children: list[DepartmentTree] = Field(default_factory=list)
