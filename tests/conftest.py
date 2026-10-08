"""Shared pytest fixtures: a TestClient on an isolated temporary database."""

from __future__ import annotations

import os
import secrets
import tempfile
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

_TEMP_DIR = tempfile.mkdtemp(prefix="library-api-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEMP_DIR}/test.db"
# Rolled per run so no API key value ever lives in the repository.
os.environ["API_KEY"] = secrets.token_hex(32)


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
