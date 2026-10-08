"""Book CRUD business logic."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models.book import Book
from app.models.loan import Loan
from app.schemas.book import BookCreate, BookUpdate


def _ensure_isbn_unique(db: Session, isbn: str, exclude_id: int | None = None) -> None:
    """Reject an ISBN already held by another book (409 duplicate_isbn)."""

    statement = select(Book).where(Book.isbn == isbn)
    if exclude_id is not None:
        statement = statement.where(Book.id != exclude_id)
    if db.scalar(statement) is not None:
        raise LibraryError(
            "duplicate_isbn",
            f"A book with ISBN {isbn!r} already exists",
            409,
        )


def _get_or_404(db: Session, book_id: int) -> Book:
    """Fetch a book by id or raise 404 not_found."""

    book = db.get(Book, book_id)
    if book is None:
        raise LibraryError("not_found", f"Book {book_id} was not found", 404)
    return book


def create_book(db: Session, data: BookCreate) -> Book:
    """Create a book, refusing a duplicate ISBN."""

    _ensure_isbn_unique(db, data.isbn)
    book = Book(
        title=data.title,
        author=data.author,
        isbn=data.isbn,
        year=data.year,
        copies=data.copies,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def get_book(db: Session, book_id: int) -> Book:
    """Fetch a book by id."""

    return _get_or_404(db, book_id)


def replace_book(db: Session, book_id: int, data: BookCreate) -> Book:
    """Replace every field of an existing book."""

    book = _get_or_404(db, book_id)
    _ensure_isbn_unique(db, data.isbn, exclude_id=book.id)
    book.title = data.title
    book.author = data.author
    book.isbn = data.isbn
    book.year = data.year
    book.copies = data.copies
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book_id: int, data: BookUpdate) -> Book:
    """Apply only the submitted fields to an existing book."""

    book = _get_or_404(db, book_id)
    changes = data.model_dump(exclude_unset=True)
    if "isbn" in changes:
        _ensure_isbn_unique(db, changes["isbn"], exclude_id=book.id)
    for field, value in changes.items():
        setattr(book, field, value)
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book_id: int) -> None:
    """Delete a book unless a loan row still references it."""

    book = _get_or_404(db, book_id)
    referenced = db.scalar(select(Loan.id).where(Loan.book_id == book.id).limit(1))
    if referenced is not None:
        raise LibraryError(
            "referenced_by_loans",
            f"Book {book_id} is referenced by existing loans",
            409,
        )
    db.delete(book)
    db.commit()
