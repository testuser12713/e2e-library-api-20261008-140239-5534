"""Loan routes (declarations only; bodies owned by the loan ticket)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, require_api_key
from app.pagination import PaginationParams, pagination_params
from app.schemas.common import Page
from app.schemas.loan import LoanCreate, LoanRead

router = APIRouter(prefix="/loans", tags=["loans"])


def _not_implemented(route: str) -> HTTPException:
    return HTTPException(status_code=501, detail=f"{route} is not implemented yet")


@router.post(
    "",
    response_model=LoanRead,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
def create_loan(data: LoanCreate, db: Session = Depends(get_db)) -> LoanRead:
    raise _not_implemented("POST /loans")


@router.get("", response_model=Page[LoanRead])
def list_loans(
    params: PaginationParams = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> Page[LoanRead]:
    raise _not_implemented("GET /loans")


@router.get("/{loan_id}", response_model=LoanRead)
def get_loan(loan_id: int, db: Session = Depends(get_db)) -> LoanRead:
    raise _not_implemented("GET /loans/{loan_id}")
