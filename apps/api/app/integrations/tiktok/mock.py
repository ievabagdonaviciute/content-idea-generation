"""Fixture-backed OwnContentProvider used when TikTok Login Kit credentials are
not configured. Reads fixtures/tiktok_posts.json -- see docs/TIKTOK_INTEGRATION.md.
"""

from __future__ import annotations

from datetime import datetime

from app.core.fixtures import load_fixture
from app.integrations.tiktok.base import CreatorProfileData, SourceVideoData


class MockTikTokProvider:
    def __init__(self) -> None:
        self._raw = load_fixture("tiktok_posts.json")

    async def get_profile(self) -> CreatorProfileData:
        profile = self._raw["creator_profile"]
        return CreatorProfileData(
            username=profile["username"],
            display_name=profile.get("display_name"),
            avatar_url=profile.get("avatar_url"),
            bio=profile.get("bio"),
            follower_count=profile.get("follower_count"),
        )

    async def list_videos(self) -> list[SourceVideoData]:
        return [
            SourceVideoData(
                external_video_id=video["external_video_id"],
                permalink=video["permalink"],
                caption=video.get("caption"),
                posted_at=datetime.fromisoformat(video["posted_at"].replace("Z", "+00:00"))
                if video.get("posted_at")
                else None,
                duration_seconds=video.get("duration_seconds"),
                stats=video.get("stats", {}),
            )
            for video in self._raw["videos"]
        ]
