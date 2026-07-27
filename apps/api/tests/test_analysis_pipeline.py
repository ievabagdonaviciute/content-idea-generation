from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.json_generation import JsonGenerationError, generate_validated_json
from app.integrations.tiktok.mock import MockTikTokProvider
from app.models.content_analysis import ContentAnalysis
from app.models.inspiration import InspirationItem
from app.models.own_post import OwnPost
from app.pipelines.analysis_pipeline import run_inspiration_analysis, run_own_post_analysis
from app.schemas.content_analysis import ContentAnalysisSchema
from app.services.tiktok_sync import TikTokSyncService


class BrokenTextProvider:
    async def generate_json(self, prompt: str, schema: object) -> str:
        return "not valid json"


async def _seed_own_posts(session: AsyncSession) -> list[OwnPost]:
    await TikTokSyncService(session, provider=MockTikTokProvider()).sync()
    result = await session.execute(select(OwnPost))
    return list(result.scalars().all())


async def test_run_own_post_analysis_creates_content_analysis(db_session: AsyncSession) -> None:
    posts = await _seed_own_posts(db_session)
    post = posts[0]

    await run_own_post_analysis(db_session, post)

    assert post.processing_status == "completed"
    assert post.processing_error is None

    analysis = (
        await db_session.execute(
            select(ContentAnalysis).where(ContentAnalysis.own_post_id == post.id)
        )
    ).scalar_one()
    assert analysis.primary_topic
    assert analysis.hook_text
    assert analysis.embedding is not None
    assert len(analysis.embedding) > 0
    # No local media is ever present in tests -- both stages must be skipped honestly
    # rather than fabricating a transcript/visual description.
    assert analysis.transcript_available is False
    assert analysis.visual_analysis_available is False


async def test_rerunning_analysis_updates_existing_row_in_place(db_session: AsyncSession) -> None:
    posts = await _seed_own_posts(db_session)
    post = posts[0]

    await run_own_post_analysis(db_session, post)
    first_analysis = (
        await db_session.execute(
            select(ContentAnalysis).where(ContentAnalysis.own_post_id == post.id)
        )
    ).scalar_one()

    await run_own_post_analysis(db_session, post)

    count = (
        await db_session.execute(
            select(func.count())
            .select_from(ContentAnalysis)
            .where(ContentAnalysis.own_post_id == post.id)
        )
    ).scalar_one()
    assert count == 1

    second_analysis = (
        await db_session.execute(
            select(ContentAnalysis).where(ContentAnalysis.own_post_id == post.id)
        )
    ).scalar_one()
    assert second_analysis.id == first_analysis.id


async def test_own_post_analysis_failure_is_recorded_without_creating_a_row(
    db_session: AsyncSession, monkeypatch
) -> None:
    posts = await _seed_own_posts(db_session)
    post = posts[0]
    monkeypatch.setattr(
        "app.pipelines.analysis_pipeline.get_text_provider", lambda: BrokenTextProvider()
    )

    await run_own_post_analysis(db_session, post)

    assert post.processing_status == "failed"
    assert post.processing_error is not None

    count = (
        await db_session.execute(
            select(func.count())
            .select_from(ContentAnalysis)
            .where(ContentAnalysis.own_post_id == post.id)
        )
    ).scalar_one()
    assert count == 0


async def test_run_inspiration_analysis_creates_content_analysis(db_session: AsyncSession) -> None:
    item = InspirationItem(
        notion_page_id="page-1",
        title="Interesting video",
        tiktok_url="https://www.tiktok.com/@someone/video/123",
        tiktok_video_id="123",
        note_why_saved="Great hook",
    )
    db_session.add(item)
    await db_session.flush()

    await run_inspiration_analysis(db_session, item)

    assert item.error_message is None
    analysis = (
        await db_session.execute(
            select(ContentAnalysis).where(ContentAnalysis.inspiration_item_id == item.id)
        )
    ).scalar_one()
    assert analysis.primary_topic


async def test_run_inspiration_analysis_records_error_on_failure(
    db_session: AsyncSession, monkeypatch
) -> None:
    item = InspirationItem(
        notion_page_id="page-2",
        title="Another video",
        tiktok_url="https://www.tiktok.com/@someone/video/456",
        tiktok_video_id="456",
    )
    db_session.add(item)
    await db_session.flush()
    monkeypatch.setattr(
        "app.pipelines.analysis_pipeline.get_text_provider", lambda: BrokenTextProvider()
    )

    await run_inspiration_analysis(db_session, item)

    assert item.error_message is not None
    count = (
        await db_session.execute(
            select(func.count())
            .select_from(ContentAnalysis)
            .where(ContentAnalysis.inspiration_item_id == item.id)
        )
    ).scalar_one()
    assert count == 0


async def test_broken_provider_raises_json_generation_error_directly() -> None:
    with pytest.raises(JsonGenerationError):
        await generate_validated_json(BrokenTextProvider(), "prompt", ContentAnalysisSchema)
