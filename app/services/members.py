"""Member CRUD service signatures, implemented by a later ticket."""

from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models.member import Member
from app.pagination import PaginationParams
from app.schemas.common import Page
from app.schemas.member import MemberCreate, MemberRead, MemberUpdate


def create_member(db: Session, data: MemberCreate) -> Member:
    """Create a member; implemented by the member-CRUD ticket."""

    raise LibraryError("not_implemented", "create_member is not implemented yet", 501)


def list_members(db: Session, params: PaginationParams) -> Page[MemberRead]:
    """List members; implemented by the member-CRUD ticket."""

    raise LibraryError("not_implemented", "list_members is not implemented yet", 501)


def get_member(db: Session, member_id: int) -> Member:
    """Fetch a member by id; implemented by the member-CRUD ticket."""

    raise LibraryError("not_implemented", "get_member is not implemented yet", 501)


def replace_member(db: Session, member_id: int, data: MemberCreate) -> Member:
    """Replace a member; implemented by the member-CRUD ticket."""

    raise LibraryError("not_implemented", "replace_member is not implemented yet", 501)


def update_member(db: Session, member_id: int, data: MemberUpdate) -> Member:
    """Partially update a member; implemented by the member-CRUD ticket."""

    raise LibraryError("not_implemented", "update_member is not implemented yet", 501)


def delete_member(db: Session, member_id: int) -> None:
    """Delete a member; implemented by the member-CRUD ticket."""

    raise LibraryError("not_implemented", "delete_member is not implemented yet", 501)
