from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
import respx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.integrations.tiktok.base import (
    CreatorProfileData,
    SourceVideoData,
    TikTokAuthError,
    TikTokNotConfiguredError,
)
from app.integrations.tiktok.mock import MockTikTokProvider
from app.integrations.tiktok.production import DISPLAY_API_BASE_URL, TikTokLoginKitProvider
from app.models.own_post import OwnPost
from app.models.source_video import SourceVideo
from app.services.tiktok_sync import TikTokSyncService


class RaisingProvider:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    async def get_profile(self) -> CreatorProfileData:
        raise self._exc

    async def list_videos(self) -> list[SourceVideoData]:
        raise self._exc


async def test_sync_creates_profile_and_posts_from_mock_fixture(db_session: AsyncSession) -> None:
    service = TikTokSyncService(db_session, provider=MockTikTokProvider())
    sync_run = await service.sync()

    assert sync_run.status == "completed"
    assert sync_run.items_processed == 8

    videos = (await db_session.execute(select(SourceVideo))).scalars().all()
    posts = (await db_session.execute(select(OwnPost))).scalars().all()
    assert len(videos) == 8
    assert len(posts) == 8
    assert all(post.processing_status == "pending" for post in posts)


async def test_incremental_sync_does_not_duplicate_or_reprocess(db_session: AsyncSession) -> None:
    service = TikTokSyncService(db_session, provider=MockTikTokProvider())
    await service.sync()

    # Simulate that one post already finished analysis.
    posts = (await db_session.execute(select(OwnPost))).scalars().all()
    posts[0].processing_status = "completed"
    await db_session.commit()

    second_run = await service.sync()
    assert second_run.status == "completed"
    assert second_run.items_processed == 8  # all videos revisited (metadata refresh)

    videos = (await db_session.execute(select(SourceVideo))).scalars().all()
    posts_after = (await db_session.execute(select(OwnPost))).scalars().all()
    assert len(videos) == 8  # no duplicates created
    assert len(posts_after) == 8
    completed = [p for p in posts_after if p.processing_status == "completed"]
    assert len(completed) == 1  # untouched by the second sync


async def test_sync_records_auth_failure_without_corrupting_existing_data(
    db_session: AsyncSession,
) -> None:
    service = TikTokSyncService(db_session, provider=MockTikTokProvider())
    await service.sync()
    videos_before = (await db_session.execute(select(SourceVideo))).scalars().all()
    assert len(videos_before) == 8

    failing_service = TikTokSyncService(
        db_session, provider=RaisingProvider(TikTokAuthError("token revoked"))
    )
    failed_run = await failing_service.sync()

    assert failed_run.status == "failed"
    assert failed_run.error_summary is not None
    assert "Authorization error" in failed_run.error_summary

    videos_after = (await db_session.execute(select(SourceVideo))).scalars().all()
    assert len(videos_after) == 8  # untouched


async def test_production_provider_requires_configuration() -> None:
    settings = Settings(
        tiktok_client_key="key", tiktok_client_secret="secret", tiktok_redirect_uri="uri"
    )
    with pytest.raises(TikTokNotConfiguredError):
        TikTokLoginKitProvider(settings, access_token=None)

    settings_no_creds = Settings()
    with pytest.raises(TikTokNotConfiguredError):
        TikTokLoginKitProvider(settings_no_creds, access_token="some-token")


@respx.mock
async def test_production_provider_paginates_video_list() -> None:
    settings = Settings(
        tiktok_client_key="key", tiktok_client_secret="secret", tiktok_redirect_uri="uri"
    )
    provider = TikTokLoginKitProvider(settings, access_token="valid-token")

    page_1 = {
        "data": {
            "videos": [
                {
                    "id": "1",
                    "video_description": "first",
                    "create_time": int(datetime(2026, 1, 1, tzinfo=UTC).timestamp()),
                    "duration": 30,
                    "share_url": "https://www.tiktok.com/@x/video/1",
                    "view_count": 10,
                    "like_count": 1,
                    "comment_count": 0,
                    "share_count": 0,
                }
            ],
            "cursor": 100,
            "has_more": True,
        }
    }
    page_2 = {
        "data": {
            "videos": [
                {
                    "id": "2",
                    "video_description": "second",
                    "create_time": int(datetime(2026, 1, 2, tzinfo=UTC).timestamp()),
                    "duration": 45,
                    "share_url": "https://www.tiktok.com/@x/video/2",
                    "view_count": 20,
                    "like_count": 2,
                    "comment_count": 1,
                    "share_count": 1,
                }
            ],
            "cursor": 200,
            "has_more": False,
        }
    }
    route = respx.post(f"{DISPLAY_API_BASE_URL}/video/list/")
    route.side_effect = [
        httpx.Response(200, json=page_1),
        httpx.Response(200, json=page_2),
    ]

    videos = await provider.list_videos()

    assert [v.external_video_id for v in videos] == ["1", "2"]
    assert route.call_count == 2


@respx.mock
async def test_production_provider_translates_401_to_auth_error() -> None:
    settings = Settings(
        tiktok_client_key="key", tiktok_client_secret="secret", tiktok_redirect_uri="uri"
    )
    provider = TikTokLoginKitProvider(settings, access_token="expired-token")
    respx.get(f"{DISPLAY_API_BASE_URL}/user/info/").mock(return_value=httpx.Response(401))

    with pytest.raises(TikTokAuthError):
        await provider.get_profile()
