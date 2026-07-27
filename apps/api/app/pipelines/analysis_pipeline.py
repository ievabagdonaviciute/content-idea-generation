"""Turns a raw OwnPost/InspirationItem into a validated ContentAnalysis row.

Implements the stage sequence from docs/AI_PIPELINE.md: ingest -> normalize ->
acquire permitted content -> (extract audio -> transcribe) -> (sample frames ->
describe) -> analyze -> store -> embed -> mark status. Each stage is a small,
independently testable function; ``_run_analysis`` composes them. Re-running
analysis on an entity that already has one updates the existing ContentAnalysis
row in place rather than inserting a second one (the model enforces exactly one
per own_post/inspiration_item).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import (
    get_embedding_provider,
    get_text_provider,
    get_transcription_provider,
    get_vision_provider,
)
from app.ai.json_generation import generate_validated_json
from app.ai.prompts.analysis_prompts import AnalysisPromptContext, build_content_analysis_prompt
from app.core.config import get_settings
from app.core.logging import get_logger
from app.integrations.tiktok.resolver import AuthorizedMediaResolver
from app.models.content_analysis import ContentAnalysis
from app.models.inspiration import InspirationItem
from app.models.media import MediaAsset
from app.models.own_post import OwnPost
from app.models.processing_job import ProcessingJob
from app.models.source_video import SourceVideo
from app.pipelines.media_processing import MediaProcessingError, extract_audio, sample_frames
from app.schemas.content_analysis import ContentAnalysisSchema

logger = get_logger(__name__)


@dataclass
class _SourceContext:
    entity_kind: str  # "own_post" | "inspiration_item"
    entity: OwnPost | InspirationItem
    video_id: str | None
    caption: str | None
    creator_notes: str | None

    @property
    def entity_id(self) -> uuid.UUID:
        return self.entity.id


async def normalize_metadata(
    session: AsyncSession, entity: OwnPost | InspirationItem
) -> _SourceContext:
    """Builds the context needed for analysis directly from the database rather
    than relying on the caller having eagerly loaded ``entity``'s relationships
    (lazy-loading a relationship from plain sync attribute access raises
    ``MissingGreenlet`` under the async ORM)."""
    if isinstance(entity, OwnPost):
        video = await session.get(SourceVideo, entity.source_video_id)
        assert video is not None
        return _SourceContext(
            entity_kind="own_post",
            entity=entity,
            video_id=video.external_video_id,
            caption=video.caption,
            creator_notes=None,
        )

    notes = "\n".join(n for n in (entity.note_why_saved, entity.note_favorite_part) if n)
    return _SourceContext(
        entity_kind="inspiration_item",
        entity=entity,
        video_id=entity.tiktok_video_id,
        caption=entity.title,
        creator_notes=notes or None,
    )


def acquire_permitted_content(video_id: str | None) -> Path | None:
    """Never guesses: only ever returns a path the user explicitly placed under
    MEDIA_STORAGE_PATH/authorized/{video_id}.mp4 (see AuthorizedMediaResolver)."""
    return AuthorizedMediaResolver(get_settings()).find_local_media(video_id)


def _add_media_asset(
    session: AsyncSession, context: _SourceContext, *, kind: str, storage_path: str
) -> None:
    session.add(
        MediaAsset(
            own_post_id=context.entity_id if context.entity_kind == "own_post" else None,
            inspiration_item_id=(
                context.entity_id if context.entity_kind == "inspiration_item" else None
            ),
            kind=kind,
            storage_path=storage_path,
        )
    )


async def extract_audio_stage(
    session: AsyncSession, context: _SourceContext, video_path: Path
) -> Path | None:
    output_path = get_settings().media_storage_dir / "derived" / f"{context.entity_id}_audio.m4a"
    try:
        audio_path = await extract_audio(video_path, output_path)
    except MediaProcessingError as exc:
        logger.error("audio_extraction_failed", entity_id=str(context.entity_id), error=str(exc))
        return None
    _add_media_asset(session, context, kind="audio_extract", storage_path=str(audio_path))
    return audio_path


async def sample_frames_stage(
    session: AsyncSession, context: _SourceContext, video_path: Path
) -> list[Path]:
    settings = get_settings()
    output_dir = settings.media_storage_dir / "derived" / f"{context.entity_id}_frames"
    try:
        frame_paths = await sample_frames(video_path, output_dir, settings.max_sample_frames)
    except MediaProcessingError as exc:
        logger.error("frame_sampling_failed", entity_id=str(context.entity_id), error=str(exc))
        return []
    for frame_path in frame_paths:
        _add_media_asset(session, context, kind="sampled_frame", storage_path=str(frame_path))
    return frame_paths


async def analyze_content(
    context: _SourceContext, transcript: str | None, visual_description: str | None
) -> ContentAnalysisSchema:
    prompt = build_content_analysis_prompt(
        AnalysisPromptContext(
            caption=context.caption,
            creator_notes=context.creator_notes,
            transcript=transcript,
            visual_description=visual_description,
            output_language=get_settings().default_output_language,
        )
    )
    return await generate_validated_json(get_text_provider(), prompt, ContentAnalysisSchema)


async def _upsert_content_analysis(
    session: AsyncSession, context: _SourceContext
) -> ContentAnalysis:
    # Queried directly by owner FK rather than via ``context.entity.content_analysis``
    # -- that relationship attribute may not be loaded on ``context.entity``
    # (lazy-loading it from plain sync attribute access raises ``MissingGreenlet``
    # under the async ORM), and this way behaves identically regardless of how the
    # caller fetched the entity.
    if isinstance(context.entity, OwnPost):
        stmt = select(ContentAnalysis).where(ContentAnalysis.own_post_id == context.entity_id)
    else:
        stmt = select(ContentAnalysis).where(
            ContentAnalysis.inspiration_item_id == context.entity_id
        )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        return existing
    # Assigning through the relationship (not just the FK column) keeps the
    # in-memory owning object's ``content_analysis`` attribute in sync via
    # back_populates.
    analysis = ContentAnalysis()
    if isinstance(context.entity, OwnPost):
        analysis.own_post = context.entity
    else:
        analysis.inspiration_item = context.entity
    return analysis


async def store_structured_features(
    session: AsyncSession,
    context: _SourceContext,
    data: ContentAnalysisSchema,
    *,
    visual_analysis_available: bool,
    transcript_available: bool,
    embedding: list[float],
) -> ContentAnalysis:
    analysis = await _upsert_content_analysis(session, context)
    analysis.primary_topic = data.primary_topic
    analysis.secondary_topics = data.secondary_topics
    analysis.content_format = data.content_format
    analysis.presentation_style = data.presentation_style
    analysis.hook_text = data.hook.text
    analysis.hook_type = data.hook.type
    analysis.hook_mechanism = data.hook.mechanism
    analysis.tone = data.tone
    analysis.story_structure = data.story_structure
    analysis.audience_promise = data.audience_promise
    analysis.emotional_angle = data.emotional_angle
    analysis.cta_pattern = data.cta_pattern
    analysis.editing_intensity = data.editing_intensity
    analysis.estimated_pacing = data.estimated_pacing
    analysis.personal_story_level = data.personal_story_level
    analysis.educational_level = data.educational_level
    analysis.visual_analysis_available = visual_analysis_available
    analysis.transcript_available = transcript_available
    analysis.confidence = data.confidence
    analysis.embedding = embedding
    session.add(analysis)
    await session.flush()
    return analysis


async def create_embeddings(data: ContentAnalysisSchema) -> list[float]:
    text = " ".join(
        [data.primary_topic, *data.secondary_topics, data.hook.text, data.audience_promise]
    )
    [embedding] = await get_embedding_provider().embed([text])
    return embedding


async def _run_analysis(session: AsyncSession, context: _SourceContext) -> ContentAnalysis:
    job = ProcessingJob(
        job_type=(
            "analyze_own_post" if context.entity_kind == "own_post" else "analyze_inspiration_item"
        ),
        status="processing",
        related_entity_type=context.entity_kind,
        related_entity_id=context.entity_id,
    )
    session.add(job)
    await session.flush()

    try:
        local_media_path = acquire_permitted_content(context.video_id)
        transcript_text: str | None = None
        transcript_available = False
        visual_description: str | None = None
        visual_analysis_available = False

        if local_media_path is not None:
            audio_path = await extract_audio_stage(session, context, local_media_path)
            if audio_path is not None:
                result = await get_transcription_provider().transcribe(audio_path)
                transcript_text = result.text
                transcript_available = True

            frame_paths = await sample_frames_stage(session, context, local_media_path)
            if frame_paths:
                visual = await get_vision_provider().describe_frames(frame_paths)
                visual_description = "; ".join(visual.frame_descriptions) or None
                visual_analysis_available = bool(visual_description)

        analysis_data = await analyze_content(context, transcript_text, visual_description)
        embedding = await create_embeddings(analysis_data)
        analysis = await store_structured_features(
            session,
            context,
            analysis_data,
            visual_analysis_available=visual_analysis_available,
            transcript_available=transcript_available,
            embedding=embedding,
        )

        job.status = "completed"
        job.result = {"content_analysis_id": str(analysis.id)}
        return analysis
    except Exception as exc:  # noqa: BLE001 -- recorded on the job/entity, never a raw 500
        job.status = "failed"
        job.error = str(exc)[:4000]
        raise


async def run_own_post_analysis(session: AsyncSession, post: OwnPost) -> None:
    post.processing_status = "processing"
    await session.flush()
    try:
        context = await normalize_metadata(session, post)
        await _run_analysis(session, context)
        post.processing_status = "completed"
        post.processing_error = None
    except Exception as exc:  # noqa: BLE001 -- persisted on the owning row
        post.processing_status = "failed"
        post.processing_error = str(exc)[:2048]
        logger.error("own_post_analysis_failed", post_id=str(post.id), error=str(exc))
    await session.flush()


async def run_inspiration_analysis(session: AsyncSession, item: InspirationItem) -> None:
    try:
        context = await normalize_metadata(session, item)
        await _run_analysis(session, context)
        item.error_message = None
    except Exception as exc:  # noqa: BLE001 -- persisted on the owning row
        item.error_message = str(exc)[:2048]
        logger.error("inspiration_analysis_failed", item_id=str(item.id), error=str(exc))
    await session.flush()
