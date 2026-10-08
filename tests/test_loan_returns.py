"""Tests for loan return and overdue listing (tickets 4)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.loan import Loan
from app.models.member import Member
from app.services.availability import available_copies


class Seed:
    """Creates and cleans up only the rows this test module owns."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self._loan_ids: list[int] = []
        self._book_ids: list[int] = []
        self._member_ids: list[int] = []

    def book(self, copies: int = 1) -> Book:
        tag = uuid.uuid4().hex
        book = Book(
            title=f"Buch {tag}",
            author="Autor",
            isbn=f"isbn-{tag}",
            year=2020,
            copies=copies,
        )
        self.session.add(book)
        self.session.commit()
        self._book_ids.append(book.id)
        return book

    def member(self) -> Member:
        tag = uuid.uuid4().hex
        member = Member(name=f"Member {tag}", email=f"{tag}@example.com")
        self.session.add(member)
        self.session.commit()
        self._member_ids.append(member.id)
        return member

    def loan(
        self,
        book: Book,
        member: Member,
        *,
        due_at: datetime | None = None,
        returned_at: datetime | None = None,
    ) -> Loan:
        now = datetime.now(UTC)
        loan = Loan(
            book_id=book.id,
            member_id=member.id,
            loaned_at=now - timedelta(days=1),
            due_at=due_at if due_at is not None else now + timedelta(days=13),
            returned_at=returned_at,
        )
        self.session.add(loan)
        self.session.commit()
        self._loan_ids.append(loan.id)
        return loan

    def open_loans_for_member(self, member_id: int) -> int:
        count = self.session.scalar(
            select(func.count())
            .select_from(Loan)
            .where(Loan.member_id == member_id, Loan.returned_at.is_(None))
        )
        return int(count or 0)

    def cleanup(self) -> None:
        if self._loan_ids:
            self.session.execute(delete(Loan).where(Loan.id.in_(self._loan_ids)))
        if self._book_ids:
            self.session.execute(delete(Book).where(Book.id.in_(self._book_ids)))
        if self._member_ids:
            self.session.execute(delete(Member).where(Member.id.in_(self._member_ids)))
        self.session.commit()
        self.session.close()


@pytest.fixture()
def seed(client: TestClient) -> Iterator[Seed]:
    """Seed rows on the real engine, after the app lifespan created the schema."""

    from app.db import get_sessionmaker

    session = get_sessionmaker()()
    helper = Seed(session)
    yield helper
    helper.cleanup()


def test_return_sets_returned_at(
    client: TestClient, auth_headers: dict[str, str], seed: Seed
) -> None:
    loan = seed.loan(seed.book(), seed.member())

    response = client.post(f"/loans/{loan.id}/return", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == loan.id
    assert body["returned_at"] is not None


def test_return_without_api_key_is_unauthorized(client: TestClient, seed: Seed) -> None:
    loan = seed.loan(seed.book(), seed.member())

    response = client.post(f"/loans/{loan.id}/return")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_return_unknown_loan_is_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post("/loans/999999/return", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_second_return_conflicts(
    client: TestClient, auth_headers: dict[str, str], seed: Seed
) -> None:
    loan = seed.loan(seed.book(), seed.member())

    first = client.post(f"/loans/{loan.id}/return", headers=auth_headers)
    second = client.post(f"/loans/{loan.id}/return", headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "already_returned"


def test_return_frees_copy_and_member_slot(
    client: TestClient, auth_headers: dict[str, str], seed: Seed
) -> None:
    book = seed.book(copies=1)
    member = seed.member()
    loan = seed.loan(book, member)

    assert available_copies(seed.session, book) == 0
    assert seed.open_loans_for_member(member.id) == 1

    response = client.post(f"/loans/{loan.id}/return", headers=auth_headers)
    assert response.status_code == 200

    seed.session.expire_all()
    assert available_copies(seed.session, book) == 1
    assert seed.open_loans_for_member(member.id) == 0


def test_overdue_lists_only_past_due_open_loans(client: TestClient, seed: Seed) -> None:
    now = datetime.now(UTC)
    book = seed.book(copies=3)
    member = seed.member()
    overdue = seed.loan(book, member, due_at=now - timedelta(days=2))
    on_time = seed.loan(book, member, due_at=now + timedelta(days=2))
    returned = seed.loan(
        book,
        member,
        due_at=now - timedelta(days=5),
        returned_at=now - timedelta(days=4),
    )

    response = client.get("/loans/overdue")

    assert response.status_code == 200
    body = response.json()
    ids = {item["id"] for item in body["items"]}
    assert overdue.id in ids
    assert on_time.id not in ids
    assert returned.id not in ids
    assert body["total"] >= len(ids)


def test_overdue_paginates(client: TestClient, seed: Seed) -> None:
    now = datetime.now(UTC)
    book = seed.book(copies=3)
    member = seed.member()
    first_loan = seed.loan(book, member, due_at=now - timedelta(days=3))
    second_loan = seed.loan(book, member, due_at=now - timedelta(days=2))
    third_loan = seed.loan(book, member, due_at=now - timedelta(days=1))
    expected = {first_loan.id, second_loan.id, third_loan.id}

    first = client.get("/loans/overdue", params={"limit": 1, "offset": 0})
    second = client.get("/loans/overdue", params={"limit": 1, "offset": 1})

    assert first.status_code == 200
    first_body = first.json()
    assert first_body["limit"] == 1
    assert first_body["offset"] == 0
    assert len(first_body["items"]) == 1
    assert first_body["items"][0]["id"] in expected
    assert first_body["total"] >= 3

    second_body = second.json()
    assert len(second_body["items"]) == 1
    assert second_body["items"][0]["id"] in expected
    assert second_body["items"][0]["id"] != first_body["items"][0]["id"]
