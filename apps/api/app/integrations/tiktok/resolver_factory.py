from __future__ import annotations

from app.core.config import get_settings
from app.core.fixtures import load_fixture
from app.core.url_validation import normalize_tiktok_url
from app.integrations.tiktok.resolver import (
    InspirationContentResolver,
    MockInspirationResolver,
    TikTokOEmbedResolver,
)


def get_inspiration_resolver() -> InspirationContentResolver:
    settings = get_settings()
    if settings.use_mock_notion:
        raw = load_fixture("notion_items.json")
        availability_by_url = {
            normalize_tiktok_url(item["tiktok_url"]): item["mock_availability"]
            for item in raw["items"]
            if item.get("tiktok_url")
        }
        return MockInspirationResolver(availability_by_url)
    return TikTokOEmbedResolver()
