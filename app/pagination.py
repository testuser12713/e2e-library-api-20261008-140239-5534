"""Shared pagination parameters and the FastAPI dependency."""

from fastapi import Query
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Validated ``limit``/``offset`` pair carried into the services."""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


def pagination_params(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginationParams:
    """FastAPI dependency that builds :class:`PaginationParams` from the query."""

    return PaginationParams(limit=limit, offset=offset)
