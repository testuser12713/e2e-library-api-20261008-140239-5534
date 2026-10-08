"""Availability calculation for books."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.loan import Loan


def available_copies(db: Session, book: Book) -> int:
    """Return book.copies minus the number of its open loans.

    An empty library must never report a negative number of free copies.
    """

    open_loans = db.scalar(
        select(func.count())
        .select_from(Loan)
        .where(Loan.book_id == book.id, Loan.returned_at.is_(None))
    )
    return max(book.copies - int(open_loans or 0), 0)
