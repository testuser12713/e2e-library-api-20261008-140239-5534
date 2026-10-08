"""Loan creation, listing and lookup service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models.book import Book
from app.models.loan import Loan
from app.models.member import Member
from app.pagination import PaginationParams
from app.schemas.common import Page
from app.schemas.loan import LoanCreate, LoanRead
from app.services.availability import available_copies

# Business rules from the spec: a loan runs for two weeks and a member may
# hold at most three open loans at a time.
LOAN_PERIOD_DAYS = 14
MAX_OPEN_LOANS = 3


def create_loan(db: Session, data: LoanCreate) -> Loan:
    """Lend one free copy of a book to a member.

    Raises :class:`LibraryError` with ``not_found`` (404) for an unknown book
    or member, ``loan_limit_reached`` (409) when the member already holds
    three open loans, and ``no_copies_available`` (409) when no copy is free.
    Nothing is written in any of the error cases.
    """

    book = db.get(Book, data.book_id)
    if book is None:
        raise LibraryError("not_found", f"Book {data.book_id} not found", 404)

    member = db.get(Member, data.member_id)
    if member is None:
        raise LibraryError("not_found", f"Member {data.member_id} not found", 404)

    open_loans = db.scalar(
        select(func.count())
        .select_from(Loan)
        .where(Loan.member_id == member.id, Loan.returned_at.is_(None))
    )
    if int(open_loans or 0) >= MAX_OPEN_LOANS:
        raise LibraryError(
            "loan_limit_reached",
            f"Member {member.id} already has {MAX_OPEN_LOANS} open loans",
            409,
        )

    if available_copies(db, book) <= 0:
        raise LibraryError(
            "no_copies_available",
            f"Book {book.id} has no free copy",
            409,
        )

    loaned_at = datetime.now(UTC)
    loan = Loan(
        book_id=book.id,
        member_id=member.id,
        loaned_at=loaned_at,
        due_at=loaned_at + timedelta(days=LOAN_PERIOD_DAYS),
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


def list_loans(db: Session, params: PaginationParams) -> Page[LoanRead]:
    """List loans newest first, paginated through ``limit``/``offset``."""

    total = db.scalar(select(func.count()).select_from(Loan)) or 0
    loans = db.scalars(
        select(Loan)
        .order_by(Loan.loaned_at.desc(), Loan.id.desc())
        .limit(params.limit)
        .offset(params.offset)
    ).all()
    return Page[LoanRead](
        items=[LoanRead.model_validate(loan) for loan in loans],
        total=int(total),
        limit=params.limit,
        offset=params.offset,
    )


def get_loan(db: Session, loan_id: int) -> Loan:
    """Fetch a loan by id, or raise ``not_found`` (404)."""

    loan = db.get(Loan, loan_id)
    if loan is None:
        raise LibraryError("not_found", f"Loan {loan_id} not found", 404)
    return loan
