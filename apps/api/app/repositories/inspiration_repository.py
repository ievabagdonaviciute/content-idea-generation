from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.inspiration import InspirationItem


class InspirationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_notion_page_id(self, notion_page_id: str) -> InspirationItem | None:
        result = await self._session.execute(
            select(InspirationItem).where(InspirationItem.notion_page_id == notion_page_id)
        )
        return result.scalar_one_or_none()

    async def get_by_tiktok_url(self, tiktok_url: str) -> InspirationItem | None:
        result = await self._session.execute(
            select(InspirationItem).where(InspirationItem.tiktok_url == tiktok_url)
        )
        return result.scalar_one_or_none()

    async def get_by_tiktok_video_id(self, video_id: str) -> InspirationItem | None:
        result = await self._session.execute(
            select(InspirationItem).where(InspirationItem.tiktok_video_id == video_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, item_id: uuid.UUID) -> InspirationItem | None:
        return await self._session.get(
            InspirationItem,
            item_id,
            options=[selectinload(InspirationItem.content_analysis)],
        )

    async def list_all(
        self, *, limit: int = 50, offset: int = 0
    ) -> list[InspirationItem]:
        result = await self._session.execute(
            select(InspirationItem)
            .order_by(InspirationItem.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_by_status(self, status: str) -> int:
        result = await self._session.execute(
            select(InspirationItem).where(InspirationItem.notion_status == status)
        )
        return len(result.scalars().all())

    def add(self, item: InspirationItem) -> None:
        self._session.add(item)
