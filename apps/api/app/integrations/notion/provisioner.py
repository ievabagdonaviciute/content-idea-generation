"""Finds or creates the Notion inspiration database inside the hardcoded page.

Implements the "First Startup" sequence from docs/NOTION_SETUP.md: extract the page
ID from ``NOTION_PAGE_URL``, look for a child database named
``NOTION_INSPIRATION_DATABASE_TITLE``, create it if missing, and add any missing
properties if it already exists. Existing properties are never modified or removed.
Idempotent and safe to call on every sync.
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.personal_config import NOTION_INSPIRATION_DATABASE_TITLE, NOTION_PAGE_URL
from app.integrations.notion.page_url import extract_page_id
from app.integrations.notion.schema import missing_properties, required_database_properties

NOTION_API_BASE_URL = "https://api.notion.com/v1"
NOTION_API_VERSION = "2022-06-28"


class NotionApiError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class NotionDatabaseProvisioner:
    def __init__(self, token: str, http_client: httpx.AsyncClient | None = None) -> None:
        self._token = token
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
        self._owns_client = http_client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def ensure_database(self) -> str:
        """Return the inspiration database ID, creating/repairing it if needed."""
        page_id = extract_page_id(NOTION_PAGE_URL)
        database_id = await self._find_existing_database(page_id)
        if database_id is None:
            database_id = await self._create_database(page_id)
        else:
            await self._ensure_schema(database_id)
        return database_id

    async def _find_existing_database(self, page_id: str) -> str | None:
        cursor: str | None = None
        while True:
            params: dict[str, str] = {"page_size": "100"}
            if cursor:
                params["start_cursor"] = cursor
            response = await self._client.get(f"/blocks/{page_id}/children", params=params)
            self._raise_for_status(response)
            body = response.json()
            for block in body.get("results", []):
                if block.get("type") == "child_database":
                    title = block.get("child_database", {}).get("title", "")
                    if title == NOTION_INSPIRATION_DATABASE_TITLE:
                        return str(block["id"])
            if not body.get("has_more"):
                return None
            cursor = body.get("next_cursor")

    async def _create_database(self, page_id: str) -> str:
        response = await self._client.post(
            "/databases",
            json={
                "parent": {"type": "page_id", "page_id": page_id},
                "title": [{"type": "text", "text": {"content": NOTION_INSPIRATION_DATABASE_TITLE}}],
                "properties": required_database_properties(),
            },
        )
        self._raise_for_status(response)
        return str(response.json()["id"])

    async def _ensure_schema(self, database_id: str) -> None:
        response = await self._client.get(f"/databases/{database_id}")
        self._raise_for_status(response)
        existing = response.json().get("properties", {})
        to_add = missing_properties(existing)
        if not to_add:
            return
        patch_response = await self._client.patch(
            f"/databases/{database_id}", json={"properties": to_add}
        )
        self._raise_for_status(patch_response)

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code >= 400:
            raise NotionApiError(
                f"Notion API error {response.status_code}: {response.text[:500]}",
                status_code=response.status_code,
            )
