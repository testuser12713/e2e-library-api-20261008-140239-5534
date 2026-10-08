"""Reusable FastAPI dependencies: database session and API-key guard."""

from __future__ import annotations

import hmac
from collections.abc import Generator

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_sessionmaker


def get_db() -> Generator[Session]:
    """Yield a database session and close it after the request."""

    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Reject every write unless a configured key matches ``X-API-Key``.

    With no key configured at all, every write is refused.
    """

    configured = get_settings().API_KEY
    if not configured or not x_api_key or not hmac.compare_digest(x_api_key, configured):
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")
