"""Loan service signatures, implemented by a later ticket."""

from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models.loan import Loan
from app.pagination import PaginationParams
from app.schemas.common import Page
from app.schemas.loan import LoanCreate, LoanRead


def create_loan(db: Session, data: LoanCreate) -> Loan:
    """Create a loan; implemented by the loan ticket."""

    raise LibraryError("not_implemented", "create_loan is not implemented yet", 501)


def list_loans(db: Session, params: PaginationParams) -> Page[LoanRead]:
    """List loans, newest first; implemented by the loan ticket."""

    raise LibraryError("not_implemented", "list_loans is not implemented yet", 501)


def get_loan(db: Session, loan_id: int) -> Loan:
    """Fetch a loan by id; implemented by the loan ticket."""

    raise LibraryError("not_implemented", "get_loan is not implemented yet", 501)
