"""Pydantic schemas for the Employee resource.

Input schemas (``*Create``) validate request bodies; ``*Read`` schemas
describe API responses and are built from ORM objects.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class EmployeeBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=1, max_length=200)
    position: str = Field(min_length=1, max_length=200)
    hired_at: date | None = None


class EmployeeCreate(EmployeeBase):
    """Request body for `POST /departments/{id}/employees/`.

    `department_id` is taken from the URL path, not from the body.
    """


class EmployeeRead(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department_id: int
    created_at: datetime
