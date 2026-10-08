"""Database engine, declarative base and session factory."""

from __future__ import annotations

import importlib
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for every ORM model."""


@lru_cache
def get_engine() -> Engine:
    """Create (once) the engine for the configured database URL."""

    settings = get_settings()
    connect_args: dict[str, object] = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(settings.DATABASE_URL, connect_args=connect_args)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    """Create (once) the session factory bound to the configured engine."""

    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def session_scope() -> Generator[Session]:
    """Yield a session and always close it."""

    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Import every model and create missing tables on the configured engine."""

    importlib.import_module("app.models")
    Base.metadata.create_all(bind=get_engine())
