"""Health endpoint and startup behavior."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import inspect


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_startup_creates_schema(client: TestClient) -> None:
    """The lifespan must create the tables on a fresh database."""

    from app.db import get_engine

    tables = set(inspect(get_engine()).get_table_names())
    assert {"books", "members", "loans"} <= tables
