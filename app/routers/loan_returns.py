"""Loan return and overdue routes (declarations only; bodies owned by the ticket).

This router is registered BEFORE the loans router so the static ``/loans/overdue``
path is matched before the dynamic ``/loans/{loan_id}`` path.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, require_api_key
from app.pagination import PaginationParams, pagination_params
from app.schemas.common import Page
from app.schemas.loan import LoanRead

router = APIRouter(prefix="/loans", tags=["loan-returns"])


def _not_implemented(route: str) -> HTTPException:
    return HTTPException(status_code=501, detail=f"{route} is not implemented yet")


@router.get("/overdue", response_model=Page[LoanRead])
def list_overdue(
    params: PaginationParams = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> Page[LoanRead]:
    raise _not_implemented("GET /loans/overdue")


@router.post(
    "/{loan_id}/return",
    response_model=LoanRead,
    dependencies=[Depends(require_api_key)],
)
def return_loan(loan_id: int, db: Session = Depends(get_db)) -> LoanRead:
    raise _not_implemented("POST /loans/{loan_id}/return")
