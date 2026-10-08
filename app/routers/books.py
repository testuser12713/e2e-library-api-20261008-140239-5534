"""Book CRUD routes (declarations only; bodies owned by the book-CRUD ticket)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, require_api_key
from app.schemas.book import BookCreate, BookRead, BookUpdate

router = APIRouter(prefix="/books", tags=["books"])


def _not_implemented(route: str) -> HTTPException:
    return HTTPException(status_code=501, detail=f"{route} is not implemented yet")


@router.post(
    "",
    response_model=BookRead,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
def create_book(data: BookCreate, db: Session = Depends(get_db)) -> BookRead:
    raise _not_implemented("POST /books")


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: int, db: Session = Depends(get_db)) -> BookRead:
    raise _not_implemented("GET /books/{book_id}")


@router.put(
    "/{book_id}",
    response_model=BookRead,
    dependencies=[Depends(require_api_key)],
)
def replace_book(book_id: int, data: BookCreate, db: Session = Depends(get_db)) -> BookRead:
    raise _not_implemented("PUT /books/{book_id}")


@router.patch(
    "/{book_id}",
    response_model=BookRead,
    dependencies=[Depends(require_api_key)],
)
def update_book(book_id: int, data: BookUpdate, db: Session = Depends(get_db)) -> BookRead:
    raise _not_implemented("PATCH /books/{book_id}")


@router.delete(
    "/{book_id}",
    status_code=204,
    dependencies=[Depends(require_api_key)],
)
def delete_book(book_id: int, db: Session = Depends(get_db)) -> None:
    raise _not_implemented("DELETE /books/{book_id}")
