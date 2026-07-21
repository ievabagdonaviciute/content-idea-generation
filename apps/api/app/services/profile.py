"""Builds a versioned ContentProfileSnapshot from every analyzed OwnPost.

A pure statistical aggregation over already-stored ContentAnalysis rows -- no AI
provider call (unlike idea/brief/script generation). Each rebuild inserts a new
row rather than overwriting the previous one, so profile history is preserved --
see the model's docstring and docs/DATA_MODEL.md.
"""

from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seed_data import CONTENT_FORMATS
from app.models.content_analysis import ContentAnalysis
from app.models.content_profile_snapshot import ContentProfileSnapshot

_MIN_CONFIDENT_SAMPLE_SIZE = 15
_OVERUSED_SHARE_THRESHOLD = 0.3


async def _fetch_own_post_analyses(session: AsyncSession) -> list[ContentAnalysis]:
    result = await session.execute(
        select(ContentAnalysis).where(ContentAnalysis.own_post_id.is_not(None))
    )
    return list(result.scalars().all())


def _distribution(counter: Counter[str], total: int, key_name: str) -> list[dict]:
    return [
        {key_name: value, "count": count, "share": round(count / total, 3)}
        for value, count in counter.most_common()
    ]


def _build_observations(
    sample_size: int,
    top_pillar: tuple[str, int] | None,
    top_format: tuple[str, int] | None,
) -> list[str]:
    if sample_size == 0:
        return ["Dar neanalizuota nė vieno įrašo -- profilis kol kas tuščias."]
    observations = [f"Iš viso analizuota {sample_size} paskelbtų įrašų."]
    if top_pillar:
        topic, count = top_pillar
        observations.append(
            f"Dažniausia tema -- {topic} ({round(count / sample_size * 100)}% įrašų)."
        )
    if top_format:
        fmt, count = top_format
        observations.append(
            f"Dažniausiai naudojamas formatas -- {fmt} ({round(count / sample_size * 100)}% įrašų)."
        )
    return observations


def _build_confidence_notes(sample_size: int) -> list[str]:
    if sample_size == 0:
        return ["Nėra analizuotų įrašų -- pasitikėjimo lygis minimalus."]
    if sample_size < _MIN_CONFIDENT_SAMPLE_SIZE:
        return [
            f"Pagrįsta tik {sample_size} įrašais -- išvados preliminarios, "
            f"pasitikėjimas augs surinkus daugiau duomenų."
        ]
    return [f"Pagrįsta {sample_size} analizuotais įrašais -- pakankama imtis pagrįstoms išvadoms."]


async def build_profile_snapshot(session: AsyncSession) -> ContentProfileSnapshot:
    analyses = await _fetch_own_post_analyses(session)
    sample_size = len(analyses)

    topic_counter = Counter(a.primary_topic for a in analyses)
    format_counter = Counter(a.content_format for a in analyses)
    hook_counter = Counter(a.hook_type for a in analyses)
    structure_counter = Counter(
        " -> ".join(a.story_structure) for a in analyses if a.story_structure
    )
    tone_counter: Counter[str] = Counter()
    for a in analyses:
        tone_counter.update(a.tone)
    combo_counter = Counter((a.content_format, a.primary_topic) for a in analyses)

    used_format_codes = set(format_counter)
    all_format_codes = {fmt["code"] for fmt in CONTENT_FORMATS}
    unused_format_codes = sorted(all_format_codes - used_format_codes)
    unused_labels = [
        fmt["label_lt"] for fmt in CONTENT_FORMATS if fmt["code"] in unused_format_codes
    ]

    polished_count = sum(1 for a in analyses if a.editing_intensity in ("medium", "high"))
    polished_vs_casual_ratio = (
        round(polished_count / sample_size, 3) if sample_size else None
    )
    personal_story_frequency = (
        round(sum(a.personal_story_level for a in analyses) / sample_size, 3)
        if sample_size
        else None
    )

    overused_topics = [
        topic
        for topic, count in topic_counter.items()
        if sample_size and count / sample_size >= _OVERUSED_SHARE_THRESHOLD
    ]

    top_pillar = topic_counter.most_common(1)[0] if topic_counter else None
    top_format = format_counter.most_common(1)[0] if format_counter else None

    overall_confidence = (
        round(min(1.0, sample_size / _MIN_CONFIDENT_SAMPLE_SIZE), 3) if sample_size else 0.0
    )

    snapshot = ContentProfileSnapshot(
        sample_size=sample_size,
        content_pillars=_distribution(topic_counter, sample_size, "topic") if sample_size else [],
        format_distribution=(
            _distribution(format_counter, sample_size, "format") if sample_size else []
        ),
        underused_formats=unused_labels,
        typical_hooks=_distribution(hook_counter, sample_size, "hook_type") if sample_size else [],
        typical_structures=(
            _distribution(structure_counter, sample_size, "pattern") if sample_size else []
        ),
        tone_distribution=(
            _distribution(tone_counter, sum(tone_counter.values()), "tone")
            if tone_counter
            else []
        ),
        polished_vs_casual_ratio=polished_vs_casual_ratio,
        personal_story_frequency=personal_story_frequency,
        recently_overused_topics=overused_topics,
        recently_uncovered_topics=unused_labels,
        frequent_combinations=[
            {"format": fmt, "topic": topic, "count": count}
            for (fmt, topic), count in combo_counter.most_common()
            if count > 1
        ],
        content_gaps=unused_labels,
        observations_lt=_build_observations(sample_size, top_pillar, top_format),
        confidence_notes=_build_confidence_notes(sample_size),
        overall_confidence=overall_confidence,
    )
    session.add(snapshot)
    await session.flush()
    return snapshot


async def get_latest_profile(session: AsyncSession) -> ContentProfileSnapshot | None:
    result = await session.execute(
        select(ContentProfileSnapshot).order_by(ContentProfileSnapshot.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()
