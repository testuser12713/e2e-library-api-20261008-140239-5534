"""Member CRUD routes (declarations only; bodies owned by the member-CRUD ticket)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, require_api_key
from app.pagination import PaginationParams, pagination_params
from app.schemas.common import Page
from app.schemas.member import MemberCreate, MemberRead, MemberUpdate

router = APIRouter(prefix="/members", tags=["members"])


def _not_implemented(route: str) -> HTTPException:
    return HTTPException(status_code=501, detail=f"{route} is not implemented yet")


@router.post(
    "",
    response_model=MemberRead,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
def create_member(data: MemberCreate, db: Session = Depends(get_db)) -> MemberRead:
    raise _not_implemented("POST /members")


@router.get("", response_model=Page[MemberRead])
def list_members(
    params: PaginationParams = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> Page[MemberRead]:
    raise _not_implemented("GET /members")


@router.get("/{member_id}", response_model=MemberRead)
def get_member(member_id: int, db: Session = Depends(get_db)) -> MemberRead:
    raise _not_implemented("GET /members/{member_id}")


@router.put(
    "/{member_id}",
    response_model=MemberRead,
    dependencies=[Depends(require_api_key)],
)
def replace_member(member_id: int, data: MemberCreate, db: Session = Depends(get_db)) -> MemberRead:
    raise _not_implemented("PUT /members/{member_id}")


@router.patch(
    "/{member_id}",
    response_model=MemberRead,
    dependencies=[Depends(require_api_key)],
)
def update_member(member_id: int, data: MemberUpdate, db: Session = Depends(get_db)) -> MemberRead:
    raise _not_implemented("PATCH /members/{member_id}")


@router.delete(
    "/{member_id}",
    status_code=204,
    dependencies=[Depends(require_api_key)],
)
def delete_member(member_id: int, db: Session = Depends(get_db)) -> None:
    raise _not_implemented("DELETE /members/{member_id}")
