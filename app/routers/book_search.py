"""Book search route: paginated listing with an optional substring filter."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db
from app.pagination import PaginationParams, pagination_params
from app.schemas.book import BookRead
from app.schemas.common import Page
from app.services.book_search import list_books as list_books_service

router = APIRouter(prefix="/books", tags=["book-search"])


@router.get("", response_model=Page[BookRead])
def list_books(
    params: PaginationParams = Depends(pagination_params),
    q: str | None = None,
    db: Session = Depends(get_db),
) -> Page[BookRead]:
    """List books, optionally filtered by a case-insensitive title/author substring."""

    return list_books_service(db, params, q)
