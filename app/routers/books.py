"""Book CRUD routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, require_api_key
from app.models.book import Book
from app.schemas.book import BookCreate, BookRead, BookUpdate
from app.services import books as books_service
from app.services.availability import available_copies

router = APIRouter(prefix="/books", tags=["books"])


def _to_read(db: Session, book: Book) -> BookRead:
    """Render a book, including its currently free copies."""

    return BookRead(
        id=book.id,
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        year=book.year,
        copies=book.copies,
        available_copies=available_copies(db, book),
    )


@router.post(
    "",
    response_model=BookRead,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
def create_book(data: BookCreate, db: Session = Depends(get_db)) -> BookRead:
    book = books_service.create_book(db, data)
    return _to_read(db, book)


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: int, db: Session = Depends(get_db)) -> BookRead:
    book = books_service.get_book(db, book_id)
    return _to_read(db, book)


@router.put(
    "/{book_id}",
    response_model=BookRead,
    dependencies=[Depends(require_api_key)],
)
def replace_book(book_id: int, data: BookCreate, db: Session = Depends(get_db)) -> BookRead:
    book = books_service.replace_book(db, book_id, data)
    return _to_read(db, book)


@router.patch(
    "/{book_id}",
    response_model=BookRead,
    dependencies=[Depends(require_api_key)],
)
def update_book(book_id: int, data: BookUpdate, db: Session = Depends(get_db)) -> BookRead:
    book = books_service.update_book(db, book_id, data)
    return _to_read(db, book)


@router.delete(
    "/{book_id}",
    status_code=204,
    dependencies=[Depends(require_api_key)],
)
def delete_book(book_id: int, db: Session = Depends(get_db)) -> None:
    books_service.delete_book(db, book_id)
