"""
Shared Pydantic v2 base schemas and utility types.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TimestampedModel(BaseModel):
    """Base schema that includes standard timestamp fields."""

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime


class UUIDModel(TimestampedModel):
    """Base schema with a UUID primary key and timestamps."""

    id: UUID


class ErrorResponse(BaseModel):
    """Standard error envelope returned by the API."""

    detail: str
    code: str | None = None
