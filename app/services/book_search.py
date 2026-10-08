"""Book search and pagination service."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.pagination import PaginationParams
from app.schemas.book import BookRead
from app.schemas.common import Page
from app.services.availability import available_copies


def _like_pattern(raw: str) -> str:
    """Build a ``LIKE`` pattern that treats ``raw`` as a literal substring.

    The user input is escaped so that ``%`` and ``_`` are matched literally
    instead of being interpreted as SQL wildcards.
    """

    escaped = raw.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def list_books(db: Session, params: PaginationParams, q: str | None = None) -> Page[BookRead]:
    """List books, filtered by an optional substring on title or author.

    The filter is a case-insensitive substring match on the title OR the author.
    Results are ordered by id and sliced by the pagination parameters. ``total``
    is the number of matching books, independent of the page size.
    """

    filters = []
    if q:
        pattern = _like_pattern(q)
        filters.append(
            or_(
                Book.title.ilike(pattern, escape="\\"),
                Book.author.ilike(pattern, escape="\\"),
            )
        )

    total = int(db.scalar(select(func.count()).select_from(Book).where(*filters)) or 0)

    statement = (
        select(Book).where(*filters).order_by(Book.id).limit(params.limit).offset(params.offset)
    )
    books = db.scalars(statement).all()

    items = [
        BookRead(
            id=book.id,
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            year=book.year,
            copies=book.copies,
            available_copies=available_copies(db, book),
        )
        for book in books
    ]

    return Page[BookRead](items=items, total=total, limit=params.limit, offset=params.offset)
