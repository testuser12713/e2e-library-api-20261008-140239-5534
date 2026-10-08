"""Member CRUD routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, require_api_key
from app.pagination import PaginationParams, pagination_params
from app.schemas.common import Page
from app.schemas.member import MemberCreate, MemberRead, MemberUpdate
from app.services import members as member_service

router = APIRouter(prefix="/members", tags=["members"])


@router.post(
    "",
    response_model=MemberRead,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
def create_member(data: MemberCreate, db: Session = Depends(get_db)) -> MemberRead:
    return MemberRead.model_validate(member_service.create_member(db, data))


@router.get("", response_model=Page[MemberRead])
def list_members(
    params: PaginationParams = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> Page[MemberRead]:
    return member_service.list_members(db, params)


@router.get("/{member_id}", response_model=MemberRead)
def get_member(member_id: int, db: Session = Depends(get_db)) -> MemberRead:
    return MemberRead.model_validate(member_service.get_member(db, member_id))


@router.put(
    "/{member_id}",
    response_model=MemberRead,
    dependencies=[Depends(require_api_key)],
)
def replace_member(member_id: int, data: MemberCreate, db: Session = Depends(get_db)) -> MemberRead:
    return MemberRead.model_validate(member_service.replace_member(db, member_id, data))


@router.patch(
    "/{member_id}",
    response_model=MemberRead,
    dependencies=[Depends(require_api_key)],
)
def update_member(member_id: int, data: MemberUpdate, db: Session = Depends(get_db)) -> MemberRead:
    return MemberRead.model_validate(member_service.update_member(db, member_id, data))


@router.delete(
    "/{member_id}",
    status_code=204,
    dependencies=[Depends(require_api_key)],
)
def delete_member(member_id: int, db: Session = Depends(get_db)) -> None:
    member_service.delete_member(db, member_id)
