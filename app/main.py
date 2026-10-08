"""FastAPI application entry point for the library API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from app.config import get_settings
from app.db import init_db
from app.errors import register_exception_handlers
from app.routers import book_search, books, loan_returns, loans, members


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Validate configuration and create the schema before serving."""

    get_settings()
    init_db()
    yield


app = FastAPI(title="Stadtbibliothek Ausleih-API", version="1.0.0", lifespan=lifespan)

register_exception_handlers(app)

app.include_router(loan_returns.router)
app.include_router(loans.router)
app.include_router(books.router)
app.include_router(book_search.router)
app.include_router(members.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, Any]:
    """Liveness probe used by the run contract."""

    return {"status": "ok"}
