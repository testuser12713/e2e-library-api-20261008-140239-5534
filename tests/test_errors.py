"""The API-key guard and the uniform error body."""

from __future__ import annotations

from fastapi.testclient import TestClient

VALID_BOOK = {"title": "T", "author": "A", "isbn": "123", "year": 2000, "copies": 1}


def test_write_without_api_key_is_refused(client: TestClient) -> None:
    response = client.post("/books", json=VALID_BOOK)
    assert response.status_code == 401
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "unauthorized"
    assert isinstance(body["error"]["message"], str)
    assert body["error"]["details"] is None


def test_write_with_wrong_api_key_is_refused(client: TestClient) -> None:
    response = client.post("/books", json=VALID_BOOK, headers={"X-API-Key": "wrong"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_write_with_valid_api_key_passes_the_guard(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post("/books", json=VALID_BOOK, headers=auth_headers)
    assert response.status_code != 401


def test_reads_are_open(client: TestClient) -> None:
    response = client.get("/books")
    assert response.status_code not in (401, 404)


def test_invalid_book_payload_uses_uniform_422(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    payload = {"title": "T", "author": "A", "isbn": "123", "year": 1200, "copies": 0}
    response = client.post("/books", json=payload, headers=auth_headers)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["error"]["message"], str)
    fields = {detail["field"] for detail in body["error"]["details"]}
    assert "year" in fields
    assert "copies" in fields


def test_invalid_member_email_uses_uniform_422(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/members",
        json={"name": "A", "email": "not-an-email"},
        headers=auth_headers,
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    fields = {detail["field"] for detail in body["error"]["details"]}
    assert "email" in fields
