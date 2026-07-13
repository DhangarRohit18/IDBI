"""
FinTwin AI — Common Pydantic Schemas
Shared request/response schemas used across multiple modules.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common config for all FinTwin schemas."""
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        populate_by_name=True,
    )


class TimestampMixin(BaseSchema):
    """Mixin for schemas with created_at/updated_at fields."""
    created_at: datetime
    updated_at: datetime


class IDMixin(BaseSchema):
    """Mixin for schemas with UUID id."""
    id: UUID


class PaginatedResponse(BaseSchema, Generic[T]):
    """Standard paginated list response."""
    items: list[T]
    total: int
    limit: int
    offset: int
    pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        limit: int,
        offset: int,
    ) -> "PaginatedResponse[T]":
        pages = (total + limit - 1) // limit if limit > 0 else 0
        return cls(items=items, total=total, limit=limit, offset=offset, pages=pages)


class SuccessResponse(BaseSchema):
    """Generic success response wrapper."""
    message: str = "Success"
    data: Any = None


class ErrorResponse(BaseSchema):
    """Standard error response format."""
    detail: str
    code: str = "ERROR"
    field_errors: dict[str, str] = {}


class PaginationParams(BaseSchema):
    """Query parameters for list pagination."""
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class TaskResponse(BaseSchema):
    """Response for async tasks submitted to Celery."""
    task_id: str
    status: str = "QUEUED"
    message: str = "Task submitted successfully"
