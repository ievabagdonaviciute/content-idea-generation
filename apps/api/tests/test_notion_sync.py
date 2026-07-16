from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.notion.client import NotionRow
from app.integrations.notion.mock import MockNotionClient
from app.integrations.tiktok.resolver import ResolvedInspirationContent
from app.integrations.tiktok.resolver_factory import get_inspiration_resolver
from app.models.inspiration import InspirationItem
from app.services.notion_sync import NotionSyncService


class FakeNotionClient:
    """Small hand-rolled NotionInspirationClient double for scenarios the fixture
    file doesn't cover (duplicate URLs across two Notion rows)."""

    def __init__(self, rows: list[NotionRow]) -> None:
        self._rows = {row.notion_page_id: row for row in rows}
        self.updates: list[dict] = []

    async def query_new_rows(self) -> list[NotionRow]:
        return [row for row in self._rows.values() if row.status == "New"]

    async def update_row(self, page_id: str, *, status: str, **kwargs) -> None:
        self._rows[page_id].status = status
        self.updates.append({"page_id": page_id, "status": status, **kwargs})


class FixedAvailabilityResolver:
    def __init__(self, availability: str) -> None:
        self._availability = availability

    async def resolve(self, url: str) -> ResolvedInspirationContent:
        from app.core.url_validation import extract_video_id, normalize_tiktok_url

        canonical = normalize_tiktok_url(url)
        return ResolvedInspirationContent(
            availability=self._availability,  # type: ignore[arg-type]
            canonical_url=canonical,
            video_id=extract_video_id(canonical),
            author_name="fixed_author",
            title="Fixed title",
            thumbnail_url="https://example.com/t.jpg",
            embed_html="<blockquote></blockquote>",
        )


async def test_sync_processes_only_new_rows_from_fixture(db_session: AsyncSession) -> None:
    notion_client = MockNotionClient()
    resolver = get_inspiration_resolver()
    service = NotionSyncService(db_session, notion_client=notion_client, resolver=resolver)

    sync_run = await service.sync()

    # fixture has 4 rows with Status == New (mock-page-001, 002, 005, 007)
    assert sync_run.items_processed == 4
    assert sync_run.items_failed == 0
    assert sync_run.status == "completed"

    result = await db_session.execute(select(InspirationItem))
    items = result.scalars().all()
    assert len(items) == 4
    assert all(item.notion_status == "Processed" for item in items)


async def test_sync_is_idempotent(db_session: AsyncSession) -> None:
    notion_client = MockNotionClient()
    resolver = get_inspiration_resolver()
    service = NotionSyncService(db_session, notion_client=notion_client, resolver=resolver)

    first_run = await service.sync()
    assert first_run.items_processed == 4

    second_run = await service.sync()
    assert second_run.items_processed == 0
    assert second_run.items_failed == 0

    result = await db_session.execute(select(InspirationItem))
    items = result.scalars().all()
    assert len(items) == 4  # no duplicates created


async def test_sync_marks_metadata_only_items(db_session: AsyncSession) -> None:
    notion_client = MockNotionClient()
    resolver = get_inspiration_resolver()
    service = NotionSyncService(db_session, notion_client=notion_client, resolver=resolver)

    await service.sync()

    result = await db_session.execute(
        select(InspirationItem).where(InspirationItem.notion_page_id == "mock-page-005")
    )
    item = result.scalar_one()
    assert item.availability == "unavailable"
    assert item.notion_status == "Processed"


async def test_sync_deduplicates_by_tiktok_video_id(db_session: AsyncSession) -> None:
    shared_url = "https://www.tiktok.com/@dupe.example/video/7300000000000000999"
    rows = [
        NotionRow(
            notion_page_id="dupe-1",
            title="First save",
            tiktok_url=shared_url,
            creator="dupe.example",
            status="New",
        ),
        NotionRow(
            notion_page_id="dupe-2",
            title="Same video saved again",
            tiktok_url=shared_url,
            creator="dupe.example",
            status="New",
        ),
    ]
    notion_client = FakeNotionClient(rows)
    resolver = FixedAvailabilityResolver("metadata_only")
    service = NotionSyncService(db_session, notion_client=notion_client, resolver=resolver)

    sync_run = await service.sync()
    assert sync_run.items_processed == 2

    result = await db_session.execute(select(InspirationItem))
    items = result.scalars().all()
    assert len(items) == 1
    assert items[0].tiktok_video_id == "7300000000000000999"


async def test_sync_marks_row_failed_on_invalid_url(db_session: AsyncSession) -> None:
    rows = [
        NotionRow(
            notion_page_id="bad-url-1",
            title="Bad link",
            tiktok_url="https://not-tiktok.example.com/video/1",
            creator=None,
            status="New",
        )
    ]
    notion_client = FakeNotionClient(rows)
    resolver = FixedAvailabilityResolver("metadata_only")
    service = NotionSyncService(db_session, notion_client=notion_client, resolver=resolver)

    sync_run = await service.sync()
    assert sync_run.items_processed == 0
    assert sync_run.items_failed == 1

    result = await db_session.execute(select(InspirationItem))
    item = result.scalar_one()
    assert item.notion_status == "Failed"
    assert item.error_message is not None
    assert notion_client.updates[-1]["status"] == "Failed"
