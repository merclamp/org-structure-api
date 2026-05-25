"""Pydantic schemas for the Employee resource.

Input schemas (``*Create``) validate request bodies; ``*Read`` schemas
describe API responses and are built from ORM objects.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class EmployeeBase(BaseModel):
    """Fields shared by employee input and output schemas."""

    # `str_strip_whitespace` trims surrounding spaces before validation,
    # so a value of only whitespace becomes "" and fails `min_length`.
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=1, max_length=200)
    position: str = Field(min_length=1, max_length=200)
    hired_at: date | None = None


class EmployeeCreate(EmployeeBase):
    """Request body for `POST /departments/{id}/employees/`.

    `department_id` is taken from the URL path, not from the body.
    """


class EmployeeRead(EmployeeBase):
    """Employee representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    department_id: int
    created_at: datetime
