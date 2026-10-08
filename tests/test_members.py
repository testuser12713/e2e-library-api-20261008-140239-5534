"""Member CRUD endpoint tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.db import get_sessionmaker
from app.models.book import Book
from app.models.loan import Loan
from app.models.member import Member


def _member_payload(name: str = "Ada Lovelace") -> dict[str, str]:
    return {"name": name, "email": f"{uuid.uuid4().hex}@example.com"}


def test_create_member_returns_201(client: TestClient, auth_headers: dict[str, str]) -> None:
    payload = {"name": "Ada Lovelace", "email": f"{uuid.uuid4().hex}@example.com"}
    response = client.post("/members", json=payload, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == payload["name"]
    assert body["email"] == payload["email"]
    assert isinstance(body["id"], int)
    assert "member_since" in body


def test_create_member_requires_api_key(client: TestClient) -> None:
    response = client.post("/members", json=_member_payload())
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_duplicate_email_is_conflict(client: TestClient, auth_headers: dict[str, str]) -> None:
    payload = _member_payload()
    first = client.post("/members", json=payload, headers=auth_headers)
    assert first.status_code == 201
    second = client.post("/members", json=payload, headers=auth_headers)
    assert second.status_code == 409
    body = second.json()
    assert body["error"]["code"] == "duplicate_email"


def test_get_member_by_id(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post("/members", json=_member_payload(), headers=auth_headers).json()
    response = client.get(f"/members/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_member_is_404(client: TestClient) -> None:
    response = client.get("/members/999999999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_list_members_is_paginated(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = []
    for index in range(3):
        response = client.post(
            "/members",
            json={"name": f"Member {index}", "email": f"{uuid.uuid4().hex}@example.com"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        created.append(response.json()["id"])

    full = client.get("/members", params={"limit": 100, "offset": 0}).json()
    page = client.get("/members", params={"limit": 1, "offset": 1}).json()

    assert page["limit"] == 1
    assert page["offset"] == 1
    assert page["total"] == full["total"]
    assert full["total"] >= len(created)
    assert len(page["items"]) == 1
    assert page["items"][0] == full["items"][1]

    ids = [item["id"] for item in full["items"]]
    assert ids == sorted(ids)


def test_replace_member(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post("/members", json=_member_payload(), headers=auth_headers).json()
    new_email = f"{uuid.uuid4().hex}@example.com"
    response = client.put(
        f"/members/{created['id']}",
        json={"name": "Grace Hopper", "email": new_email},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["name"] == "Grace Hopper"
    assert body["email"] == new_email


def test_replace_with_duplicate_email_is_conflict(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    first = client.post("/members", json=_member_payload(), headers=auth_headers).json()
    second = client.post("/members", json=_member_payload(), headers=auth_headers).json()
    response = client.put(
        f"/members/{second['id']}",
        json={"name": "Someone", "email": first["email"]},
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_email"


def test_update_member_partially(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post("/members", json=_member_payload(), headers=auth_headers).json()
    response = client.patch(
        f"/members/{created['id']}",
        json={"name": "Grace Hopper"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Grace Hopper"
    assert body["email"] == created["email"]


def test_update_with_duplicate_email_is_conflict(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    first = client.post("/members", json=_member_payload(), headers=auth_headers).json()
    second = client.post("/members", json=_member_payload(), headers=auth_headers).json()
    response = client.patch(
        f"/members/{second['id']}",
        json={"email": first["email"]},
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_email"


def test_delete_member_returns_204(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post("/members", json=_member_payload(), headers=auth_headers).json()
    response = client.delete(f"/members/{created['id']}", headers=auth_headers)
    assert response.status_code == 204
    assert client.get(f"/members/{created['id']}").status_code == 404


def test_delete_unknown_member_is_404(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.delete("/members/999999999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_delete_member_referenced_by_loan_is_conflict(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    member = client.post("/members", json=_member_payload(), headers=auth_headers).json()

    session = get_sessionmaker()()
    try:
        book = Book(title="Dune", author="Frank Herbert", isbn=uuid.uuid4().hex, year=1965)
        session.add(book)
        session.commit()
        loan = Loan(
            book_id=book.id,
            member_id=member["id"],
            due_at=datetime.now(UTC) + timedelta(days=14),
        )
        session.add(loan)
        session.commit()
        loan_id = loan.id
        book_id = book.id
        member_id = member["id"]
    finally:
        session.close()

    response = client.delete(f"/members/{member['id']}", headers=auth_headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "referenced_by_loans"

    cleanup = get_sessionmaker()()
    try:
        cleanup.delete(cleanup.get(Loan, loan_id))
        cleanup.commit()
        cleanup.delete(cleanup.get(Member, member_id))
        cleanup.delete(cleanup.get(Book, book_id))
        cleanup.commit()
    finally:
        cleanup.close()
