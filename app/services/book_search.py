"""Book search service signature, implemented by a later ticket."""

from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.pagination import PaginationParams
from app.schemas.book import BookRead
from app.schemas.common import Page


def list_books(db: Session, params: PaginationParams, q: str | None = None) -> Page[BookRead]:
    """List books, filtered by an optional substring on title or author."""

    raise LibraryError("not_implemented", "list_books is not implemented yet", 501)
