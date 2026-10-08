"""Tests for GET /books: substring search and pagination (AC-17, AC-18)."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import get_sessionmaker
from app.models.book import Book


@pytest.fixture()
def make_books(client: TestClient) -> Iterator[Callable[[list[dict[str, Any]]], list[int]]]:
    """Insert books straight into the database and remove them afterwards.

    Going through the ORM instead of ``POST /books`` keeps this suite
    independent of the book-CRUD ticket, which may not be merged yet.
    """

    created: list[int] = []

    def _make(entries: list[dict[str, Any]]) -> list[int]:
        session = get_sessionmaker()()
        try:
            books = [Book(**entry) for entry in entries]
            session.add_all(books)
            session.commit()
            ids = [book.id for book in books]
            created.extend(ids)
            return ids
        finally:
            session.close()

    yield _make

    session = get_sessionmaker()()
    try:
        session.execute(delete(Book).where(Book.id.in_(created)))
        session.commit()
    finally:
        session.close()


def test_search_matches_author_only(
    client: TestClient, make_books: Callable[[list[dict[str, Any]]], list[int]]
) -> None:
    token = uuid.uuid4().hex
    ids = make_books(
        [
            {
                "title": "Refactoring",
                "author": f"Martin {token}",
                "isbn": f"isbn-a-{token}",
                "year": 1999,
                "copies": 2,
            },
            {
                "title": "Clean Code",
                "author": f"Robert {token}",
                "isbn": f"isbn-b-{token}",
                "year": 2008,
                "copies": 1,
            },
        ]
    )

    response = client.get("/books", params={"q": f"Martin {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [item["id"] for item in body["items"]] == [ids[0]]
    assert body["items"][0]["available_copies"] == 2
    assert body["limit"] == 20
    assert body["offset"] == 0


def test_search_is_case_insensitive(
    client: TestClient, make_books: Callable[[list[dict[str, Any]]], list[int]]
) -> None:
    token = uuid.uuid4().hex
    make_books(
        [
            {
                "title": f"Stein{token}zeit",
                "author": "Anna Beispiel",
                "isbn": f"isbn-c-{token}",
                "year": 2001,
                "copies": 1,
            },
            {
                "title": "Clean Code",
                "author": f"Robert {token}",
                "isbn": f"isbn-d-{token}",
                "year": 2008,
                "copies": 1,
            },
        ]
    )

    lower = client.get("/books", params={"q": f"stein{token}"})
    upper = client.get("/books", params={"q": f"STEIN{token}".upper()})

    assert lower.status_code == 200
    assert upper.status_code == 200
    assert lower.json()["total"] == 1
    assert lower.json()["items"] == upper.json()["items"]


def test_pagination_reports_full_total(
    client: TestClient, make_books: Callable[[list[dict[str, Any]]], list[int]]
) -> None:
    token = uuid.uuid4().hex
    ids = make_books(
        [
            {
                "title": f"Werk {index} {token}",
                "author": f"Autor {index}",
                "isbn": f"isbn-{token}-{index}",
                "year": 2000,
                "copies": 1,
            }
            for index in range(5)
        ]
    )

    first = client.get("/books", params={"q": token, "limit": 2, "offset": 0})
    second = client.get("/books", params={"q": token, "limit": 2, "offset": 2})

    assert first.status_code == 200
    assert second.status_code == 200

    first_body = first.json()
    assert first_body["total"] == 5
    assert first_body["limit"] == 2
    assert first_body["offset"] == 0
    assert [item["id"] for item in first_body["items"]] == ids[:2]

    second_body = second.json()
    assert second_body["total"] == 5
    assert second_body["limit"] == 2
    assert second_body["offset"] == 2
    assert [item["id"] for item in second_body["items"]] == ids[2:4]


def test_search_without_match_returns_empty_page(
    client: TestClient, make_books: Callable[[list[dict[str, Any]]], list[int]]
) -> None:
    token = uuid.uuid4().hex
    make_books(
        [
            {
                "title": f"Steinzeit {token}",
                "author": "Anna Beispiel",
                "isbn": f"isbn-e-{token}",
                "year": 2001,
                "copies": 1,
            }
        ]
    )

    response = client.get("/books", params={"q": f"kein-treffer-{token}"})

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


def test_list_without_query_returns_page_envelope(
    client: TestClient, make_books: Callable[[list[dict[str, Any]]], list[int]]
) -> None:
    token = uuid.uuid4().hex
    ids = make_books(
        [
            {
                "title": f"Einzelband {token}",
                "author": "Autor",
                "isbn": f"isbn-f-{token}",
                "year": 2010,
                "copies": 3,
            }
        ]
    )

    response = client.get("/books", params={"limit": 100, "offset": 0})

    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 100
    assert body["offset"] == 0
    assert body["total"] >= 1
    assert ids[0] in [item["id"] for item in body["items"]]
