"""Tests for loan creation, listing and detail."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_sessionmaker
from app.models.book import Book
from app.models.loan import Loan
from app.models.member import Member
from app.services.availability import available_copies


@pytest.fixture()
def db_session(client: TestClient) -> Session:
    """A session against the same database the app under test uses."""

    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _clean_loans(db_session: Session) -> None:
    """Start every test from an empty loans table (our own table only)."""

    db_session.query(Loan).delete()
    db_session.commit()


def _make_book(db: Session, copies: int = 1) -> Book:
    book = Book(
        title="Der Steppenwolf",
        author="Hermann Hesse",
        isbn=uuid.uuid4().hex,
        year=1927,
        copies=copies,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def _make_member(db: Session) -> Member:
    member = Member(name="Ada Lovelace", email=f"{uuid.uuid4().hex}@example.com")
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def _insert_loan(db: Session, book: Book, member: Member, loaned_at: datetime) -> Loan:
    loan = Loan(
        book_id=book.id,
        member_id=member.id,
        loaned_at=loaned_at,
        due_at=loaned_at + timedelta(days=14),
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


def test_create_loan_requires_api_key(client: TestClient, db_session: Session) -> None:
    book = _make_book(db_session)
    member = _make_member(db_session)

    resp = client.post("/loans", json={"book_id": book.id, "member_id": member.id})

    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


def test_create_loan_success_sets_due_date_and_frees_copy(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    book = _make_book(db_session, copies=2)
    member = _make_member(db_session)
    before = available_copies(db_session, book)

    resp = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": member.id},
        headers=auth_headers,
    )

    assert resp.status_code == 201
    body = resp.json()
    loaned_at = datetime.fromisoformat(body["loaned_at"])
    due_at = datetime.fromisoformat(body["due_at"])
    assert due_at - loaned_at == timedelta(days=14)
    assert body["book_id"] == book.id
    assert body["member_id"] == member.id
    assert body["returned_at"] is None

    db_session.expire_all()
    assert available_copies(db_session, db_session.get(Book, book.id)) == before - 1


def test_create_loan_unknown_book_returns_404(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    member = _make_member(db_session)

    resp = client.post(
        "/loans",
        json={"book_id": 999999, "member_id": member.id},
        headers=auth_headers,
    )

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_create_loan_unknown_member_returns_404(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    book = _make_book(db_session)

    resp = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": 999999},
        headers=auth_headers,
    )

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_create_loan_refused_at_three_open_loans(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    member = _make_member(db_session)
    base = datetime(2024, 1, 1, tzinfo=UTC)
    for _ in range(3):
        book = _make_book(db_session)
        _insert_loan(db_session, book, member, base)
    db_session.commit()

    extra_book = _make_book(db_session)
    resp = client.post(
        "/loans",
        json={"book_id": extra_book.id, "member_id": member.id},
        headers=auth_headers,
    )

    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "loan_limit_reached"
    assert db_session.query(Loan).count() == 3


def test_create_loan_returned_loans_do_not_count_towards_limit(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    member = _make_member(db_session)
    past = datetime(2024, 1, 1, tzinfo=UTC)
    for _ in range(3):
        book = _make_book(db_session)
        loan = _insert_loan(db_session, book, member, past)
        loan.returned_at = past + timedelta(days=7)
    db_session.commit()

    book = _make_book(db_session)
    resp = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": member.id},
        headers=auth_headers,
    )

    assert resp.status_code == 201


def test_create_loan_without_free_copy_returns_409(
    client: TestClient, auth_headers: dict[str, str], db_session: Session
) -> None:
    book = _make_book(db_session, copies=1)
    first_member = _make_member(db_session)
    second_member = _make_member(db_session)

    first = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": first_member.id},
        headers=auth_headers,
    )
    assert first.status_code == 201

    resp = client.post(
        "/loans",
        json={"book_id": book.id, "member_id": second_member.id},
        headers=auth_headers,
    )

    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "no_copies_available"
    assert db_session.query(Loan).count() == 1


def test_list_loans_newest_first_and_paginated(client: TestClient, db_session: Session) -> None:
    book = _make_book(db_session, copies=5)
    member = _make_member(db_session)
    base = datetime(2024, 1, 1, tzinfo=UTC)
    oldest = _insert_loan(db_session, book, member, base)
    middle = _insert_loan(db_session, book, member, base + timedelta(days=1))
    newest = _insert_loan(db_session, book, member, base + timedelta(days=2))

    resp = client.get("/loans")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert [item["id"] for item in body["items"]] == [newest.id, middle.id, oldest.id]

    page = client.get("/loans", params={"limit": 2, "offset": 1}).json()
    assert page["total"] == 3
    assert page["limit"] == 2
    assert page["offset"] == 1
    assert [item["id"] for item in page["items"]] == [middle.id, oldest.id]


def test_get_loan_by_id(client: TestClient, db_session: Session) -> None:
    book = _make_book(db_session)
    member = _make_member(db_session)
    loan = _insert_loan(db_session, book, member, datetime(2024, 5, 1, tzinfo=UTC))

    resp = client.get(f"/loans/{loan.id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == loan.id
    assert body["book_id"] == book.id
    assert body["member_id"] == member.id


def test_get_unknown_loan_returns_404(client: TestClient) -> None:
    resp = client.get("/loans/999999")

    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"
