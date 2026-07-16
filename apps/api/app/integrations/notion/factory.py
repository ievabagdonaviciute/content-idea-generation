from __future__ import annotations

from app.core.config import get_settings
from app.integrations.notion.client import NotionClient, NotionInspirationClient
from app.integrations.notion.mock import MockNotionClient


def get_notion_client() -> NotionInspirationClient:
    settings = get_settings()
    if settings.use_mock_notion:
        return MockNotionClient()
    assert settings.notion_token is not None
    return NotionClient(settings.notion_token)
