"""Book CRUD: create, read, replace, partial update, delete."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.db import get_sessionmaker
from app.models.loan import Loan


def _book(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Der Steppenwolf",
        "author": "Hermann Hesse",
        "isbn": "978-3-518-36675-2",
        "year": 1927,
        "copies": 3,
    }
    payload.update(overrides)
    return payload


def _add_loan(book_id: int) -> None:
    """Insert a loan row so the book is referenced by a historical loan."""

    session = get_sessionmaker()()
    try:
        session.add(
            Loan(
                book_id=book_id,
                member_id=1,
                due_at=datetime.now(UTC) + timedelta(days=14),
            )
        )
        session.commit()
    finally:
        session.close()


def test_create_book_returns_201_with_body(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post("/books", json=_book(isbn="isbn-create-1"), headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Der Steppenwolf"
    assert body["author"] == "Hermann Hesse"
    assert body["isbn"] == "isbn-create-1"
    assert body["year"] == 1927
    assert body["copies"] == 3
    assert body["available_copies"] == 3
    assert isinstance(body["id"], int)


def test_create_book_requires_api_key(client: TestClient) -> None:
    response = client.post("/books", json=_book(isbn="isbn-no-key"))
    assert response.status_code == 401


def test_create_book_rejects_duplicate_isbn(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    payload = _book(isbn="isbn-dup-1")
    assert client.post("/books", json=payload, headers=auth_headers).status_code == 201
    response = client.post("/books", json=payload, headers=auth_headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_isbn"


def test_get_book_returns_all_fields(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post(
        "/books", json=_book(isbn="isbn-get-1", copies=5), headers=auth_headers
    ).json()
    response = client.get(f"/books/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == created["title"]
    assert body["author"] == created["author"]
    assert body["isbn"] == "isbn-get-1"
    assert body["year"] == 1927
    assert body["copies"] == 5
    assert body["available_copies"] == 5


def test_get_unknown_book_is_404(client: TestClient) -> None:
    response = client.get("/books/999999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_replace_book_overwrites_every_field(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    created = client.post("/books", json=_book(isbn="isbn-put-1"), headers=auth_headers).json()
    response = client.put(
        f"/books/{created['id']}",
        json=_book(
            title="Neuer Titel", author="Neue Autorin", isbn="isbn-put-1", year=2001, copies=2
        ),
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Neuer Titel"
    assert body["author"] == "Neue Autorin"
    assert body["year"] == 2001
    assert body["copies"] == 2
    assert body["available_copies"] == 2


def test_replace_unknown_book_is_404(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.put(
        "/books/999999", json=_book(isbn="isbn-put-missing"), headers=auth_headers
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_replace_book_rejects_duplicate_isbn(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    client.post("/books", json=_book(isbn="isbn-put-dup-a"), headers=auth_headers)
    second = client.post("/books", json=_book(isbn="isbn-put-dup-b"), headers=auth_headers).json()
    response = client.put(
        f"/books/{second['id']}",
        json=_book(isbn="isbn-put-dup-a"),
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_isbn"


def test_patch_changes_only_submitted_fields(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    created = client.post("/books", json=_book(isbn="isbn-patch-1"), headers=auth_headers).json()
    response = client.patch(
        f"/books/{created['id']}",
        json={"copies": 9},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["copies"] == 9
    assert body["title"] == created["title"]
    assert body["author"] == created["author"]
    assert body["isbn"] == created["isbn"]
    assert body["year"] == created["year"]


def test_patch_unknown_book_is_404(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.patch("/books/999999", json={"title": "X"}, headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_patch_book_rejects_duplicate_isbn(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    client.post("/books", json=_book(isbn="isbn-patch-dup-a"), headers=auth_headers)
    second = client.post("/books", json=_book(isbn="isbn-patch-dup-b"), headers=auth_headers).json()
    response = client.patch(
        f"/books/{second['id']}",
        json={"isbn": "isbn-patch-dup-a"},
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_isbn"


def test_delete_book_removes_it(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post("/books", json=_book(isbn="isbn-delete-1"), headers=auth_headers).json()
    response = client.delete(f"/books/{created['id']}", headers=auth_headers)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/books/{created['id']}").status_code == 404


def test_delete_unknown_book_is_404(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.delete("/books/999999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_delete_book_referenced_by_loan_is_409(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    created = client.post("/books", json=_book(isbn="isbn-ref-1"), headers=auth_headers).json()
    _add_loan(created["id"])
    response = client.delete(f"/books/{created['id']}", headers=auth_headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "referenced_by_loans"
    assert client.get(f"/books/{created['id']}").status_code == 200
