"""Loan return and overdue routes.

This router is registered BEFORE the loans router so the static ``/loans/overdue``
path is matched before the dynamic ``/loans/{loan_id}`` path.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, require_api_key
from app.pagination import PaginationParams, pagination_params
from app.schemas.common import Page
from app.schemas.loan import LoanRead
from app.services import loan_returns as loan_returns_service

router = APIRouter(prefix="/loans", tags=["loan-returns"])


@router.get("/overdue", response_model=Page[LoanRead])
def list_overdue(
    params: PaginationParams = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> Page[LoanRead]:
    """List open loans past their due date."""

    return loan_returns_service.list_overdue(db, params)


@router.post(
    "/{loan_id}/return",
    response_model=LoanRead,
    dependencies=[Depends(require_api_key)],
)
def return_loan(loan_id: int, db: Session = Depends(get_db)) -> LoanRead:
    """Return a loan, freeing its copy and the member's loan slot."""

    loan = loan_returns_service.return_loan(db, loan_id)
    return LoanRead.model_validate(loan)
