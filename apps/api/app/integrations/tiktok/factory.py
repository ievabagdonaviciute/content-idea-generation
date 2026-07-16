from __future__ import annotations

from app.core.config import get_settings
from app.integrations.tiktok.base import OwnContentProvider
from app.integrations.tiktok.mock import MockTikTokProvider
from app.integrations.tiktok.production import TikTokLoginKitProvider


def get_own_content_provider(access_token: str | None = None) -> OwnContentProvider:
    settings = get_settings()
    if settings.use_mock_tiktok:
        return MockTikTokProvider()
    return TikTokLoginKitProvider(settings, access_token)
