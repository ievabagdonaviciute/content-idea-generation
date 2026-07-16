"""Test configuration.

Forces every external integration to its mock/fake mode *before* any ``app`` module
is imported, regardless of what is in the developer's local ``.env`` -- tests must
never call real TikTok, Notion, or AI APIs (see docs/PRIVACY_AND_SECURITY.md and the
project testing requirements). ``get_settings()`` is process-cached, and some model
modules read it at import time (e.g. the embedding column dimension), so these
environment overrides must be the very first thing this file does.
"""

from __future__ import annotations

import os

os.environ["NOTION_TOKEN"] = ""
os.environ["TIKTOK_CLIENT_KEY"] = ""
os.environ["TIKTOK_CLIENT_SECRET"] = ""
os.environ["TIKTOK_REDIRECT_URI"] = ""
os.environ["AI_API_KEY"] = ""
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.models import Base  # noqa: E402


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()
