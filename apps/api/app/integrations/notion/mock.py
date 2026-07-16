"""Fixture-backed Notion client used when NOTION_TOKEN is not configured.

Reads fixtures/notion_items.json into memory once and mutates it in place, so a
full sync-then-inspect cycle works without any network access or Notion account.
State resets on process restart, which is expected for a mock used in local dev.
"""

from __future__ import annotations

import copy
from datetime import datetime

from app.core.fixtures import load_fixture
from app.integrations.notion.client import NotionRow

MOCK_DATABASE_ID = "mock-database-tiktok-inspiration"


class MockNotionClient:
    def __init__(self) -> None:
        raw = load_fixture("notion_items.json")
        self._items: dict[str, dict] = {
            item["notion_page_id"]: copy.deepcopy(item) for item in raw["items"]
        }

    def mock_availability_for(self, tiktok_url: str) -> str | None:
        for item in self._items.values():
            if item["tiktok_url"] == tiktok_url:
                return item.get("mock_availability")
        return None

    async def query_new_rows(self) -> list[NotionRow]:
        return [
            self._to_row(item) for item in self._items.values() if item["status"] == "New"
        ]

    async def query_all_rows(self) -> list[NotionRow]:
        """Extra helper (not part of the Protocol) used by the seed command to load
        every fixture row, including ones already Processed/Failed, as a baseline
        demo state."""
        return [self._to_row(item) for item in self._items.values()]

    async def update_row(
        self,
        page_id: str,
        *,
        status: str,
        processed_at: datetime | None = None,
        error_message: str | None = None,
        topics: list[str] | None = None,
        format_hint: str | None = None,
    ) -> None:
        item = self._items[page_id]
        item["status"] = status
        if processed_at is not None:
            item["processed_at"] = processed_at.isoformat()
        if error_message is not None:
            item["error_message"] = error_message
        if topics:
            item["topics"] = topics
        if format_hint:
            item["format_hint"] = format_hint

    @staticmethod
    def _to_row(item: dict) -> NotionRow:
        return NotionRow(
            notion_page_id=item["notion_page_id"],
            title=item.get("title"),
            tiktok_url=item.get("tiktok_url"),
            creator=item.get("creator"),
            topics=list(item.get("topics") or []),
            format_hint=item.get("format_hint"),
            note_why_saved=item.get("note_why_saved"),
            note_favorite_part=item.get("note_favorite_part"),
            status=item.get("status", "New"),
            added_at=None,
        )
