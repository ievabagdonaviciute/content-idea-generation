"""The interface the rest of the app depends on for "my own TikTok content".

Nothing outside this package should ever branch on whether it's talking to the mock
adapter or the real TikTok Login Kit / Display API adapter -- both implement
``OwnContentProvider`` and return the same plain DTOs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass
class CreatorProfileData:
    username: str
    display_name: str | None
    avatar_url: str | None
    bio: str | None
    follower_count: int | None


@dataclass
class SourceVideoData:
    external_video_id: str
    permalink: str
    caption: str | None
    posted_at: datetime | None
    duration_seconds: int | None
    stats: dict = field(default_factory=dict)


class TikTokAuthError(RuntimeError):
    """Raised when TikTok reports the stored authorization is revoked or expired."""


class TikTokNotConfiguredError(RuntimeError):
    """Raised by the production adapter when required credentials/token are absent.

    Kadro never pretends that entering a username alone grants access to TikTok
    video data -- this error is the explicit, honest alternative to silently
    returning empty results. See docs/TIKTOK_INTEGRATION.md.
    """


class OwnContentProvider(Protocol):
    async def get_profile(self) -> CreatorProfileData: ...

    async def list_videos(self) -> list[SourceVideoData]: ...
