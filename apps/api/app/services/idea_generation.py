"""Retrieval-augmented idea generation. See docs/AI_PIPELINE.md "Idea
generation": pulls summarized (never raw/whole-database) retrieval context,
assigns a novelty bucket per idea from the configured mixture, generates and
validates one ContentIdea per bucket, runs it through the similarity checker,
and persists auditable IdeaSource rows recording exactly what was retrieved.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.factory import get_embedding_provider, get_text_provider
from app.ai.json_generation import generate_validated_json
from app.ai.prompts.idea_prompts import IdeaPromptContext, build_idea_prompt
from app.core.config import Settings, get_settings
from app.models.content_profile_snapshot import ContentProfileSnapshot
from app.models.idea import ContentIdea, IdeaFeedback, IdeaSource
from app.models.inspiration import InspirationItem
from app.schemas.idea import ContentIdeaSchema
from app.services.profile import get_latest_profile
from app.services.similarity import SimilarPost, categorize, find_similar_posts

_NOVELTY_LEVELS = ("aligned", "stretch", "experimental")


@dataclass
class IdeaGenerationRequest:
    count: int = 3
    content_pillar: str | None = None
    recommended_format: str | None = None
    instructions: str | None = None
    excluded_subjects: list[str] = field(default_factory=list)
    output_language: str | None = None


def _assign_novelty_buckets(count: int, settings: Settings) -> list[str]:
    ratios = {
        "aligned": settings.idea_mix_aligned_ratio,
        "stretch": settings.idea_mix_stretch_ratio,
        "experimental": settings.idea_mix_experimental_ratio,
    }
    raw_counts = {level: ratio * count for level, ratio in ratios.items()}
    counts = {level: int(raw) for level, raw in raw_counts.items()}
    remainder = count - sum(counts.values())
    by_largest_remainder = sorted(
        ratios, key=lambda level: raw_counts[level] - counts[level], reverse=True
    )
    for level in by_largest_remainder[:remainder]:
        counts[level] += 1
    buckets = [level for level in _NOVELTY_LEVELS for _ in range(counts[level])]
    return buckets[:count]


def _summarize_profile(profile: ContentProfileSnapshot | None) -> str:
    if profile is None or profile.sample_size == 0:
        return "No profile built yet -- treat as a new creator with no established pattern."
    pillars = ", ".join(
        f"{p['topic']} ({p['share'] * 100:.0f}%)" for p in profile.content_pillars[:5]
    )
    formats = ", ".join(
        f"{f['format']} ({f['share'] * 100:.0f}%)" for f in profile.format_distribution[:5]
    )
    return (
        f"Sample size: {profile.sample_size}. Top pillars: {pillars or 'none'}. "
        f"Top formats: {formats or 'none'}. Underused formats: "
        f"{', '.join(profile.underused_formats[:5]) or 'none'}."
    )


def _summarize_similar_posts(rows: list[SimilarPost]) -> str:
    if not rows:
        return "No analyzed own posts yet."
    return "; ".join(
        f"{analysis.primary_topic} / {analysis.content_format} / hook: {analysis.hook_text}"
        for _, analysis, _ in rows
    )


def _summarize_inspiration(items: list[InspirationItem]) -> str:
    parts = []
    for item in items:
        analysis = item.content_analysis
        if analysis is not None:
            parts.append(f"{analysis.primary_topic} ({item.title or item.tiktok_url})")
        elif item.title:
            parts.append(item.title)
    return "; ".join(parts)


def _summarize_feedback(entries: list[IdeaFeedback]) -> str:
    return "; ".join(f"{e.rating}{(': ' + e.comment) if e.comment else ''}" for e in entries)


async def _fetch_recent_inspiration(session: AsyncSession, *, limit: int) -> list[InspirationItem]:
    result = await session.execute(
        select(InspirationItem)
        .where(InspirationItem.notion_status == "Processed")
        .options(selectinload(InspirationItem.content_analysis))
        .order_by(InspirationItem.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def _fetch_recent_feedback(session: AsyncSession, *, limit: int) -> list[IdeaFeedback]:
    result = await session.execute(
        select(IdeaFeedback).order_by(IdeaFeedback.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def _generate_one_idea(
    session: AsyncSession,
    *,
    bucket: str,
    profile: ContentProfileSnapshot | None,
    similar_posts: list[SimilarPost],
    inspiration_items: list[InspirationItem],
    feedback_entries: list[IdeaFeedback],
    request: IdeaGenerationRequest,
    output_language: str,
) -> ContentIdea:
    prompt = build_idea_prompt(
        IdeaPromptContext(
            novelty_level=bucket,
            profile_summary=_summarize_profile(profile),
            similar_posts_summary=_summarize_similar_posts(similar_posts),
            inspiration_summary=_summarize_inspiration(inspiration_items),
            feedback_summary=_summarize_feedback(feedback_entries),
            instructions=request.instructions,
            excluded_subjects=request.excluded_subjects,
            output_language=output_language,
        )
    )
    data = await generate_validated_json(get_text_provider(), prompt, ContentIdeaSchema)

    embedding_text = f"{data.content_pillar} {data.title} {' '.join(data.hook_options)}"
    [idea_embedding] = await get_embedding_provider().embed([embedding_text])

    closest_matches = await find_similar_posts(session, idea_embedding, limit=1)
    if closest_matches:
        closest_post, closest_analysis, score = closest_matches[0]
        same_topic = closest_analysis.primary_topic == data.content_pillar
        category = categorize(score, same_topic=same_topic)
        closest_post_id = closest_post.id
    else:
        score = 0.0
        category = "new"
        closest_post_id = None

    idea = ContentIdea(
        title=data.title,
        concept=data.concept,
        content_pillar=data.content_pillar,
        recommended_format=data.recommended_format,
        format_label_lt=data.format_label_lt,
        why_it_fits_me=data.why_it_fits_me,
        inspiration_pattern=data.inspiration_pattern,
        originality_note=data.originality_note,
        closest_existing_post_id=closest_post_id,
        similarity_score=score,
        similarity_category=category,
        novelty_level=bucket,
        hook_options=data.hook_options,
        outline=data.outline,
        suggested_duration_seconds=data.suggested_duration_seconds,
        production_effort=data.production_effort,
        output_language=output_language,
        embedding=idea_embedding,
    )
    session.add(idea)
    await session.flush()

    # Set the idea_id FK directly and session.add() rather than appending to
    # idea.sources: idea.sources is an unloaded collection on this
    # just-flushed object, and appending to it would trigger a lazy-load
    # query, which crashes in this async context (unlike the scalar
    # relationship fix in app/pipelines/analysis_pipeline.py). Nothing reads
    # idea.sources back in this same request, so the FK alone is sufficient.
    seen_post_ids = set()
    for post, _, _ in similar_posts:
        if post.id in seen_post_ids:
            continue
        seen_post_ids.add(post.id)
        session.add(IdeaSource(idea_id=idea.id, own_post_id=post.id, role="identity_reference"))
    if closest_post_id is not None and closest_post_id not in seen_post_ids:
        session.add(
            IdeaSource(idea_id=idea.id, own_post_id=closest_post_id, role="similarity_neighbor")
        )
    for item in inspiration_items:
        if item.content_analysis is not None:
            session.add(
                IdeaSource(
                    idea_id=idea.id, inspiration_item_id=item.id, role="inspiration_reference"
                )
            )
    await session.flush()
    return idea


async def generate_ideas(
    session: AsyncSession, request: IdeaGenerationRequest
) -> list[ContentIdea]:
    settings = get_settings()
    output_language = request.output_language or settings.default_output_language

    profile = await get_latest_profile(session)
    query_terms = [request.content_pillar, request.recommended_format, request.instructions]
    query_text = " ".join(filter(None, query_terms)) or "general content ideas"
    [query_embedding] = await get_embedding_provider().embed([query_text])
    similar_posts = await find_similar_posts(session, query_embedding, limit=5)
    inspiration_items = await _fetch_recent_inspiration(session, limit=10)
    feedback_entries = await _fetch_recent_feedback(session, limit=10)

    buckets = _assign_novelty_buckets(request.count, settings)
    ideas = []
    for bucket in buckets:
        idea = await _generate_one_idea(
            session,
            bucket=bucket,
            profile=profile,
            similar_posts=similar_posts,
            inspiration_items=inspiration_items,
            feedback_entries=feedback_entries,
            request=request,
            output_language=output_language,
        )
        ideas.append(idea)
    return ideas
