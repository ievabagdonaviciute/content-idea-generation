"""TikTok own-content sync. Works identically against the mock and production
adapters, since both implement ``OwnContentProvider``. See
docs/TIKTOK_INTEGRATION.md for what each adapter does and does not provide.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.integrations.tiktok.base import (
    CreatorProfileData,
    OwnContentProvider,
    SourceVideoData,
    TikTokAuthError,
)
from app.integrations.tiktok.factory import get_own_content_provider
from app.models.creator_profile import CreatorProfile
from app.models.external_account import ExternalAccount
from app.models.own_post import OwnPost
from app.models.source_video import SourceVideo
from app.models.sync_run import SyncRun
from app.repositories.own_content_repository import OwnContentRepository

logger = get_logger(__name__)


class TikTokSyncService:
    def __init__(self, session: AsyncSession, provider: OwnContentProvider | None = None) -> None:
        self._session = session
        self._repo = OwnContentRepository(session)
        self._provider = provider

    async def sync(self) -> SyncRun:
        started_at = _now()
        try:
            provider = self._provider or await self._build_provider()
            profile_data = await provider.get_profile()
            creator_profile = await self._ensure_creator_profile(profile_data)

            videos = await provider.list_videos()
            processed = 0
            for video in videos:
                await self._upsert_source_video(creator_profile.id, video)
                processed += 1

            sync_run = SyncRun(
                source="tiktok",
                status="completed",
                started_at=started_at,
                finished_at=_now(),
                items_processed=processed,
                items_failed=0,
            )
            self._session.add(sync_run)
            await self._session.commit()
            return sync_run
        except TikTokAuthError as exc:
            return await self._fail_sync(started_at, f"Authorization error: {exc}")
        except Exception as exc:  # noqa: BLE001 -- always recorded as a failed SyncRun
            logger.error("tiktok_sync_failed", error=str(exc))
            return await self._fail_sync(started_at, str(exc))

    async def _build_provider(self) -> OwnContentProvider:
        external_account = await self._repo.get_external_account(provider="tiktok")
        access_token = external_account.access_token if external_account else None
        return get_own_content_provider(access_token)

    async def _fail_sync(self, started_at: datetime, error_summary: str) -> SyncRun:
        # Roll back any partial writes from this attempt -- previously committed
        # SourceVideo/OwnPost rows from earlier successful syncs are untouched.
        await self._session.rollback()
        sync_run = SyncRun(
            source="tiktok",
            status="failed",
            started_at=started_at,
            finished_at=_now(),
            items_processed=0,
            items_failed=0,
            error_summary=error_summary[:4000],
        )
        self._session.add(sync_run)
        await self._session.commit()
        return sync_run

    async def _ensure_creator_profile(self, profile_data: CreatorProfileData) -> CreatorProfile:
        external_account = await self._repo.get_external_account(provider="tiktok")
        if external_account is None:
            external_account = ExternalAccount(provider="tiktok", is_active=True)
            self._session.add(external_account)
            await self._session.flush()

        creator_profile = await self._repo.get_creator_profile(external_account.id)
        if creator_profile is None:
            creator_profile = CreatorProfile(
                external_account_id=external_account.id, username=profile_data.username
            )
            self._session.add(creator_profile)

        creator_profile.username = profile_data.username
        creator_profile.display_name = profile_data.display_name
        creator_profile.avatar_url = profile_data.avatar_url
        creator_profile.bio = profile_data.bio
        creator_profile.follower_count = profile_data.follower_count
        await self._session.flush()
        return creator_profile

    async def _upsert_source_video(
        self, creator_profile_id: uuid.UUID, video: SourceVideoData
    ) -> None:
        existing = await self._repo.get_source_video_by_external_id(video.external_video_id)
        if existing is not None:
            # Already synced -- refresh cheap metadata (view counts etc. change
            # constantly) but never touch the linked OwnPost/analysis, so an
            # unchanged video is never reprocessed.
            existing.permalink = video.permalink
            existing.caption = video.caption
            existing.stats = video.stats
            existing.last_synced_at = _now()
            return

        source_video = SourceVideo(
            creator_profile_id=creator_profile_id,
            external_video_id=video.external_video_id,
            permalink=video.permalink,
            caption=video.caption,
            posted_at=video.posted_at,
            duration_seconds=video.duration_seconds,
            stats=video.stats,
            last_synced_at=_now(),
        )
        self._session.add(source_video)
        await self._session.flush()

        own_post = OwnPost(source_video_id=source_video.id, processing_status="pending")
        self._session.add(own_post)
        await self._session.flush()


def _now() -> datetime:
    return datetime.now(UTC)
