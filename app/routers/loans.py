"""Loan routes: create, list and detail."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, require_api_key
from app.models.loan import Loan
from app.pagination import PaginationParams, pagination_params
from app.schemas.common import Page
from app.schemas.loan import LoanCreate, LoanRead
from app.services import loans as loan_service

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post(
    "",
    response_model=LoanRead,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
def create_loan(data: LoanCreate, db: Session = Depends(get_db)) -> Loan:
    """Lend a copy of a book to a member."""

    return loan_service.create_loan(db, data)


@router.get("", response_model=Page[LoanRead])
def list_loans(
    params: PaginationParams = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> Page[LoanRead]:
    """List loans newest first, paginated."""

    return loan_service.list_loans(db, params)


@router.get("/{loan_id}", response_model=LoanRead)
def get_loan(loan_id: int, db: Session = Depends(get_db)) -> Loan:
    """Return a single loan by id."""

    return loan_service.get_loan(db, loan_id)
