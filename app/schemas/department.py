"""Pydantic schemas for the Department resource."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.employee import EmployeeRead


class DepartmentBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)


class DepartmentCreate(DepartmentBase):
    parent_id: int | None = None


class DepartmentUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = None


class DepartmentRead(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int | None
    created_at: datetime


class DepartmentTree(BaseModel):
    department: DepartmentRead
    employees: list[EmployeeRead] = Field(default_factory=list)
    children: list[DepartmentTree] = Field(default_factory=list)
