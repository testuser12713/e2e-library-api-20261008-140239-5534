"""Book search route (declaration only; body owned by the search ticket)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.pagination import PaginationParams, pagination_params
from app.schemas.book import BookRead
from app.schemas.common import Page

router = APIRouter(prefix="/books", tags=["book-search"])


@router.get("", response_model=Page[BookRead])
def list_books(
    params: PaginationParams = Depends(pagination_params),
    q: str | None = None,
    db: Session = Depends(get_db),
) -> Page[BookRead]:
    raise HTTPException(status_code=501, detail="GET /books is not implemented yet")
