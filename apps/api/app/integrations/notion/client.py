"""Notion inspiration-database client: query New rows, write back status/results.

The database itself is never manually configured -- ``NotionClient`` resolves its ID
through ``NotionDatabaseProvisioner`` on first use and caches it in-process.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

import httpx

from app.core.config import get_settings
from app.integrations.notion.provisioner import (
    NOTION_API_BASE_URL,
    NOTION_API_VERSION,
    NotionDatabaseProvisioner,
)
from app.integrations.notion.schema import (
    PROP_ADDED,
    PROP_ALREADY_USED,
    PROP_CREATOR,
    PROP_FAVORITE_PART,
    PROP_FORMAT,
    PROP_PROCESSED_AT,
    PROP_PROCESSING_ERROR,
    PROP_STATUS,
    PROP_TITLE,
    PROP_TOPIC,
    PROP_URL,
    PROP_WHY_SAVED,
)


@dataclass
class NotionRow:
    notion_page_id: str
    title: str | None
    tiktok_url: str | None
    creator: str | None
    topics: list[str] = field(default_factory=list)
    format_hint: str | None = None
    note_why_saved: str | None = None
    note_favorite_part: str | None = None
    status: str = "New"
    added_at: datetime | None = None


class NotionInspirationClient(Protocol):
    async def query_new_rows(self) -> list[NotionRow]: ...

    async def update_row(
        self,
        page_id: str,
        *,
        status: str,
        processed_at: datetime | None = None,
        error_message: str | None = None,
        topics: list[str] | None = None,
        format_hint: str | None = None,
        already_used: bool | None = None,
    ) -> None: ...


def _plain_text(rich_text_list: list[dict[str, Any]]) -> str | None:
    text = "".join(item.get("plain_text", "") for item in rich_text_list)
    return text or None


def parse_notion_page(page: dict[str, Any]) -> NotionRow:
    props = page["properties"]
    title_items = props.get(PROP_TITLE, {}).get("title", [])
    url_prop = props.get(PROP_URL, {}).get("url")
    creator_text = _plain_text(props.get(PROP_CREATOR, {}).get("rich_text", []))
    topic_options = props.get(PROP_TOPIC, {}).get("multi_select", [])
    format_option = props.get(PROP_FORMAT, {}).get("select")
    why_saved = _plain_text(props.get(PROP_WHY_SAVED, {}).get("rich_text", []))
    favorite_part = _plain_text(props.get(PROP_FAVORITE_PART, {}).get("rich_text", []))
    status_option = props.get(PROP_STATUS, {}).get("select")
    added_raw = props.get(PROP_ADDED, {}).get("created_time")

    return NotionRow(
        notion_page_id=page["id"],
        title=_plain_text(title_items),
        tiktok_url=url_prop,
        creator=creator_text,
        topics=[opt["name"] for opt in topic_options],
        format_hint=format_option["name"] if format_option else None,
        note_why_saved=why_saved,
        note_favorite_part=favorite_part,
        status=status_option["name"] if status_option else "New",
        added_at=datetime.fromisoformat(added_raw.replace("Z", "+00:00")) if added_raw else None,
    )


class NotionClient:
    """Real Notion API client, used when ``NOTION_TOKEN`` is configured."""

    def __init__(self, token: str, http_client: httpx.AsyncClient | None = None) -> None:
        settings = get_settings()
        self._client = http_client or httpx.AsyncClient(
            base_url=NOTION_API_BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_API_VERSION,
                "Content-Type": "application/json",
            },
            timeout=settings.http_timeout_seconds,
        )
        self._provisioner = NotionDatabaseProvisioner(token, http_client=self._client)
        self._database_id: str | None = None

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _get_database_id(self) -> str:
        if self._database_id is None:
            self._database_id = await self._provisioner.ensure_database()
        return self._database_id

    async def query_new_rows(self) -> list[NotionRow]:
        database_id = await self._get_database_id()
        rows: list[NotionRow] = []
        cursor: str | None = None
        while True:
            payload: dict[str, Any] = {
                "filter": {"property": PROP_STATUS, "select": {"equals": "New"}}
            }
            if cursor:
                payload["start_cursor"] = cursor
            response = await self._client.post(f"/databases/{database_id}/query", json=payload)
            response.raise_for_status()
            body = response.json()
            rows.extend(parse_notion_page(page) for page in body.get("results", []))
            if not body.get("has_more"):
                break
            cursor = body.get("next_cursor")
        return rows

    async def update_row(
        self,
        page_id: str,
        *,
        status: str,
        processed_at: datetime | None = None,
        error_message: str | None = None,
        topics: list[str] | None = None,
        format_hint: str | None = None,
        already_used: bool | None = None,
    ) -> None:
        # Ensures the database (and its property schema) exists before writing to a
        # page inside it. update_row never needs the ID for the PATCH itself, but
        # unlike query_new_rows it was otherwise never triggering schema
        # provisioning, so a newly added property (e.g. already_used) would never
        # get created on an existing database until some other call happened to run
        # query_new_rows first.
        await self._get_database_id()
        properties: dict[str, Any] = {PROP_STATUS: {"select": {"name": status}}}
        if processed_at is not None:
            properties[PROP_PROCESSED_AT] = {"date": {"start": processed_at.isoformat()}}
        if error_message is not None:
            properties[PROP_PROCESSING_ERROR] = {
                "rich_text": [{"type": "text", "text": {"content": error_message[:2000]}}]
            }
        if topics:
            properties[PROP_TOPIC] = {"multi_select": [{"name": t} for t in topics]}
        if format_hint:
            properties[PROP_FORMAT] = {"select": {"name": format_hint}}
        if already_used is not None:
            properties[PROP_ALREADY_USED] = {"checkbox": already_used}
        response = await self._client.patch(f"/pages/{page_id}", json={"properties": properties})
        response.raise_for_status()
