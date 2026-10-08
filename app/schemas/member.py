"""Member request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class MemberCreate(BaseModel):
    """Payload to create or fully replace a member."""

    name: str = Field(min_length=1)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value


class MemberUpdate(BaseModel):
    """Payload to partially update a member; every field is optional."""

    name: str | None = Field(default=None, min_length=1)
    email: EmailStr | None = None

    @field_validator("name")
    @classmethod
    def _not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("must not be empty")
        return value


class MemberRead(BaseModel):
    """A member as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    member_since: datetime
