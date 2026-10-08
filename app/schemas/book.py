"""Book request and response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Earliest plausible printed publication year (Gutenberg's press). AC-20 requires
# a year of 1200 to be rejected, so the lower bound has to sit above 1200.
MIN_PUBLICATION_YEAR = 1450


class _BookFields(BaseModel):
    """Validation rules shared by the book write schemas."""

    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    isbn: str = Field(min_length=1)
    year: int = Field(ge=MIN_PUBLICATION_YEAR)
    copies: int = Field(ge=1)

    @field_validator("title", "author", "isbn")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value


class BookCreate(_BookFields):
    """Payload to create or fully replace a book."""


class BookUpdate(BaseModel):
    """Payload to partially update a book; every field is optional."""

    title: str | None = Field(default=None, min_length=1)
    author: str | None = Field(default=None, min_length=1)
    isbn: str | None = Field(default=None, min_length=1)
    year: int | None = Field(default=None, ge=MIN_PUBLICATION_YEAR)
    copies: int | None = Field(default=None, ge=1)

    @field_validator("title", "author", "isbn")
    @classmethod
    def _not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("must not be empty")
        return value


class BookRead(BaseModel):
    """A book as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    isbn: str
    year: int
    copies: int
    available_copies: int
