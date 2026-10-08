"""Shared response schemas."""

from pydantic import BaseModel


class Page[T](BaseModel):
    """Envelope for a paginated list response."""

    items: list[T]
    total: int
    limit: int
    offset: int
