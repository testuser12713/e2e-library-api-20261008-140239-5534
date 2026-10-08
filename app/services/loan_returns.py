"""Loan return and overdue service signatures, implemented by a later ticket."""

from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models.loan import Loan
from app.pagination import PaginationParams
from app.schemas.common import Page
from app.schemas.loan import LoanRead


def return_loan(db: Session, loan_id: int) -> Loan:
    """Close a loan by id; implemented by the loan-return ticket."""

    raise LibraryError("not_implemented", "return_loan is not implemented yet", 501)


def list_overdue(db: Session, params: PaginationParams) -> Page[LoanRead]:
    """List open loans past their due date; implemented by the loan-return ticket."""

    raise LibraryError("not_implemented", "list_overdue is not implemented yet", 501)
