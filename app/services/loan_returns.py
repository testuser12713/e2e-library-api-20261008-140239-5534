"""Loan return and overdue service.

Returning a loan sets ``returned_at`` to the current UTC time. Because every
availability and slot calculation counts loans whose ``returned_at`` is NULL,
this single write frees the copy and the member's loan slot again.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models.loan import Loan
from app.pagination import PaginationParams
from app.schemas.common import Page
from app.schemas.loan import LoanRead


def return_loan(db: Session, loan_id: int) -> Loan:
    """Close a loan by id and return it.

    Raises :class:`LibraryError` with ``not_found`` (404) for an unknown loan and
    with ``already_returned`` (409) when the loan was already returned.
    """

    loan = db.get(Loan, loan_id)
    if loan is None:
        raise LibraryError("not_found", f"Loan {loan_id} not found", 404)
    if loan.returned_at is not None:
        raise LibraryError(
            "already_returned",
            f"Loan {loan_id} has already been returned",
            409,
        )

    loan.returned_at = datetime.now(UTC)
    db.commit()
    db.refresh(loan)
    return loan


def list_overdue(db: Session, params: PaginationParams) -> Page[LoanRead]:
    """List open loans whose due date lies in the past, paginated.

    A loan is overdue exactly when it has not been returned (``returned_at`` is
    NULL) and its ``due_at`` is strictly before the current UTC time.
    """

    now = datetime.now(UTC)
    conditions = (Loan.returned_at.is_(None), Loan.due_at < now)

    total = db.scalar(select(func.count()).select_from(Loan).where(*conditions)) or 0
    rows = db.scalars(
        select(Loan)
        .where(*conditions)
        .order_by(Loan.due_at.asc(), Loan.id.asc())
        .limit(params.limit)
        .offset(params.offset)
    ).all()

    items = [LoanRead.model_validate(row) for row in rows]
    return Page[LoanRead](
        items=items,
        total=int(total),
        limit=params.limit,
        offset=params.offset,
    )
