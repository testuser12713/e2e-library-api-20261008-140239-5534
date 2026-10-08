"""Shared pytest fixtures: a TestClient on an isolated temporary database."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

_TEMP_DIR = tempfile.mkdtemp(prefix="library-api-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEMP_DIR}/test.db"
os.environ["API_KEY"] = "test-api-key"


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """A TestClient that runs the app lifespan (schema creation) for real."""

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    """Headers carrying the configured API key for write requests."""

    return {"X-API-Key": os.environ["API_KEY"]}
