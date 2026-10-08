"""Member CRUD service."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import LibraryError
from app.models.loan import Loan
from app.models.member import Member
from app.pagination import PaginationParams
from app.schemas.common import Page
from app.schemas.member import MemberCreate, MemberRead, MemberUpdate


def _duplicate_email_error(email: str) -> LibraryError:
    return LibraryError(
        "duplicate_email",
        f"A member with e-mail '{email}' already exists",
        409,
    )


def _get_or_404(db: Session, member_id: int) -> Member:
    member = db.get(Member, member_id)
    if member is None:
        raise LibraryError("not_found", f"Member {member_id} not found", 404)
    return member


def _email_taken(db: Session, email: str, exclude_id: int | None = None) -> bool:
    statement = select(Member.id).where(Member.email == email)
    if exclude_id is not None:
        statement = statement.where(Member.id != exclude_id)
    return db.scalar(statement) is not None


def create_member(db: Session, data: MemberCreate) -> Member:
    """Create a member, rejecting a duplicate e-mail with 409."""

    if _email_taken(db, data.email):
        raise _duplicate_email_error(data.email)
    member = Member(name=data.name, email=data.email)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def list_members(db: Session, params: PaginationParams) -> Page[MemberRead]:
    """Return one deterministic page of members plus the total count."""

    total = db.scalar(select(func.count()).select_from(Member)) or 0
    members = db.scalars(
        select(Member).order_by(Member.id).limit(params.limit).offset(params.offset)
    ).all()
    items = [MemberRead.model_validate(member) for member in members]
    return Page[MemberRead](
        items=items,
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


def get_member(db: Session, member_id: int) -> Member:
    """Fetch a member by id or raise 404."""

    return _get_or_404(db, member_id)


def replace_member(db: Session, member_id: int, data: MemberCreate) -> Member:
    """Fully replace a member's name and e-mail."""

    member = _get_or_404(db, member_id)
    if data.email != member.email and _email_taken(db, data.email, exclude_id=member_id):
        raise _duplicate_email_error(data.email)
    member.name = data.name
    member.email = data.email
    db.commit()
    db.refresh(member)
    return member


def update_member(db: Session, member_id: int, data: MemberUpdate) -> Member:
    """Partially update the provided member fields."""

    member = _get_or_404(db, member_id)
    if data.email is not None and data.email != member.email:
        if _email_taken(db, data.email, exclude_id=member_id):
            raise _duplicate_email_error(data.email)
        member.email = data.email
    if data.name is not None:
        member.name = data.name
    db.commit()
    db.refresh(member)
    return member


def delete_member(db: Session, member_id: int) -> None:
    """Delete a member unless a loan still references it."""

    member = _get_or_404(db, member_id)
    has_loan = db.scalar(select(Loan.id).where(Loan.member_id == member_id).limit(1))
    if has_loan is not None:
        raise LibraryError(
            "referenced_by_loans",
            f"Member {member_id} is referenced by existing loans",
            409,
        )
    db.delete(member)
    db.commit()
