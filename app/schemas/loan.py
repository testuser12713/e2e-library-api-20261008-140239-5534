"""Loan request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LoanCreate(BaseModel):
    """Payload to create a loan."""

    book_id: int
    member_id: int


class LoanRead(BaseModel):
    """A loan as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    member_id: int
    loaned_at: datetime
    due_at: datetime
    returned_at: datetime | None = None
