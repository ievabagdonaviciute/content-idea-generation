"""Shared FastAPI dependencies."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session

DbSession = AsyncGenerator[AsyncSession, None]


async def get_session() -> DbSession:
    async for session in get_db_session():
        yield session
