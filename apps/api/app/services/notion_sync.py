"""Notion inspiration-inbox sync pipeline.

Implements the sequence from docs/NOTION_SETUP.md: query New rows, validate and
normalize the URL, dedupe, create/update the local record, flip the Notion row to
Processing, resolve content, flip to Processed/Failed. Idempotent: rows already
Processing/Processed/Failed are simply not returned by ``query_new_rows`` again
unless the user resets a row's Status back to New in Notion.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.url_validation import extract_video_id, normalize_tiktok_url
from app.integrations.notion.client import NotionInspirationClient, NotionRow
from app.integrations.notion.factory import get_notion_client
from app.integrations.tiktok.resolver import InspirationContentResolver
from app.integrations.tiktok.resolver_factory import get_inspiration_resolver
from app.models.inspiration import InspirationItem
from app.models.sync_run import SyncRun
from app.repositories.inspiration_repository import InspirationRepository

logger = get_logger(__name__)


class NotionSyncService:
    def __init__(
        self,
        session: AsyncSession,
        notion_client: NotionInspirationClient | None = None,
        resolver: InspirationContentResolver | None = None,
    ) -> None:
        self._session = session
        self._notion_client = notion_client or get_notion_client()
        self._resolver = resolver or get_inspiration_resolver()
        self._repo = InspirationRepository(session)

    async def sync(self) -> SyncRun:
        sync_run = SyncRun(source="notion", status="processing", started_at=_now())
        self._session.add(sync_run)
        await self._session.flush()

        rows = await self._notion_client.query_new_rows()
        processed = 0
        failed = 0

        for row in rows:
            try:
                await self._process_row(row)
                processed += 1
            except Exception as exc:  # noqa: BLE001 -- recorded per-row, sync continues
                failed += 1
                logger.error(
                    "notion_sync_row_failed", notion_page_id=row.notion_page_id, error=str(exc)
                )
                await self._mark_row_failed(row, str(exc))

        sync_run.status = "completed"
        sync_run.finished_at = _now()
        sync_run.items_processed = processed
        sync_run.items_failed = failed
        await self._session.commit()
        return sync_run

    async def _process_row(self, row: NotionRow) -> None:
        if not row.tiktok_url:
            raise ValueError("Row has no TikTok URL")

        canonical_url = normalize_tiktok_url(row.tiktok_url)
        video_id = extract_video_id(canonical_url)

        item = await self._find_existing(video_id, canonical_url)
        if item is None:
            item = InspirationItem(notion_page_id=row.notion_page_id, tiktok_url=canonical_url)
            self._repo.add(item)
        else:
            item.notion_page_id = row.notion_page_id

        item.title = row.title
        item.tiktok_video_id = video_id
        item.creator_name = row.creator
        item.topics = row.topics or None
        item.format_hint = row.format_hint
        item.note_why_saved = row.note_why_saved
        item.note_favorite_part = row.note_favorite_part
        item.notion_status = "Processing"
        await self._session.flush()

        await self._notion_client.update_row(row.notion_page_id, status="Processing")

        resolved = await self._resolver.resolve(canonical_url)
        item.availability = resolved.availability
        item.thumbnail_url = resolved.thumbnail_url
        item.embed_html = resolved.embed_html
        if not item.title and resolved.title:
            item.title = resolved.title
        if not item.creator_name and resolved.author_name:
            item.creator_name = resolved.author_name

        item.notion_status = "Processed"
        item.processed_at = _now()
        item.error_message = None
        await self._session.flush()

        await self._notion_client.update_row(
            row.notion_page_id, status="Processed", processed_at=item.processed_at
        )

    async def _find_existing(
        self, video_id: str | None, canonical_url: str
    ) -> InspirationItem | None:
        if video_id:
            existing = await self._repo.get_by_tiktok_video_id(video_id)
            if existing is not None:
                return existing
        return await self._repo.get_by_tiktok_url(canonical_url)

    async def _mark_row_failed(self, row: NotionRow, error_message: str) -> None:
        item = await self._repo.get_by_notion_page_id(row.notion_page_id)
        if item is not None:
            item.notion_status = "Failed"
            item.error_message = error_message
        else:
            item = InspirationItem(
                notion_page_id=row.notion_page_id,
                tiktok_url=row.tiktok_url or "",
                notion_status="Failed",
                error_message=error_message,
            )
            self._repo.add(item)
        await self._session.flush()
        try:
            await self._notion_client.update_row(
                row.notion_page_id, status="Failed", error_message=error_message
            )
        except Exception as exc:  # noqa: BLE001 -- Notion write failure must not crash sync
            logger.error(
                "notion_status_writeback_failed",
                notion_page_id=row.notion_page_id,
                error=str(exc),
            )


def _now() -> datetime:
    return datetime.now(UTC)
