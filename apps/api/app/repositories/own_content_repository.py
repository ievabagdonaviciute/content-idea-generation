from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.creator_profile import CreatorProfile
from app.models.external_account import ExternalAccount
from app.models.own_post import OwnPost
from app.models.source_video import SourceVideo


class OwnContentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_external_account(self, provider: str) -> ExternalAccount | None:
        result = await self._session.execute(
            select(ExternalAccount).where(ExternalAccount.provider == provider)
        )
        return result.scalar_one_or_none()

    async def get_creator_profile(self, external_account_id: uuid.UUID) -> CreatorProfile | None:
        result = await self._session.execute(
            select(CreatorProfile).where(
                CreatorProfile.external_account_id == external_account_id
            )
        )
        return result.scalar_one_or_none()

    async def get_source_video_by_external_id(self, external_video_id: str) -> SourceVideo | None:
        result = await self._session.execute(
            select(SourceVideo).where(SourceVideo.external_video_id == external_video_id)
        )
        return result.scalar_one_or_none()

    async def get_own_post_by_id(self, post_id: uuid.UUID) -> OwnPost | None:
        result = await self._session.execute(
            select(OwnPost)
            .where(OwnPost.id == post_id)
            .options(
                selectinload(OwnPost.source_video), selectinload(OwnPost.content_analysis)
            )
        )
        return result.scalar_one_or_none()

    async def list_own_posts(self, *, limit: int = 50, offset: int = 0) -> list[OwnPost]:
        result = await self._session.execute(
            select(OwnPost)
            .options(
                selectinload(OwnPost.source_video), selectinload(OwnPost.content_analysis)
            )
            .join(OwnPost.source_video)
            .order_by(SourceVideo.posted_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_own_posts(self) -> int:
        result = await self._session.execute(select(OwnPost))
        return len(result.scalars().all())
