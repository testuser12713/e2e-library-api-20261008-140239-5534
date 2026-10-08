"""Book CRUD service signatures, implemented by a later ticket."""

from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate


def create_book(db: Session, data: BookCreate) -> Book:
    """Create a book; implemented by the book-CRUD ticket."""

    raise LibraryError("not_implemented", "create_book is not implemented yet", 501)


def get_book(db: Session, book_id: int) -> Book:
    """Fetch a book by id; implemented by the book-CRUD ticket."""

    raise LibraryError("not_implemented", "get_book is not implemented yet", 501)


def replace_book(db: Session, book_id: int, data: BookCreate) -> Book:
    """Replace a book; implemented by the book-CRUD ticket."""

    raise LibraryError("not_implemented", "replace_book is not implemented yet", 501)


def update_book(db: Session, book_id: int, data: BookUpdate) -> Book:
    """Partially update a book; implemented by the book-CRUD ticket."""

    raise LibraryError("not_implemented", "update_book is not implemented yet", 501)


def delete_book(db: Session, book_id: int) -> None:
    """Delete a book; implemented by the book-CRUD ticket."""

    raise LibraryError("not_implemented", "delete_book is not implemented yet", 501)
