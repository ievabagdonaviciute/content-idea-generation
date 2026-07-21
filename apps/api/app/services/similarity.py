"""Cosine similarity + score-to-category mapping used by idea generation to flag
duplicates against the creator's own published posts. See docs/AI_PIPELINE.md
"Embeddings and similarity". Dialect-aware: pgvector ``<=>`` ORDER BY on Postgres,
an in-Python cosine loop over fetched rows on SQLite (see docs/ARCHITECTURE.md).
"""

from __future__ import annotations

import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.models.content_analysis import ContentAnalysis
from app.models.own_post import OwnPost

SimilarPost = tuple[OwnPost, ContentAnalysis, float]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def categorize(score: float, *, same_topic: bool, settings: Settings | None = None) -> str:
    """Topic-only overlap with a different format/angle is never auto-rejected --
    a same-topic match in the "related" band is a ``follow_up``, a different-topic
    one is ``related_but_distinct``; only the top band is ``too_similar``."""
    settings = settings or get_settings()
    if score >= settings.similarity_too_similar_threshold:
        return "too_similar"
    if score >= settings.similarity_related_threshold:
        return "follow_up" if same_topic else "related_but_distinct"
    return "new"


async def find_similar_posts(
    session: AsyncSession, query_embedding: list[float], *, limit: int = 5
) -> list[SimilarPost]:
    """Nearest own posts (by ContentAnalysis.embedding) to ``query_embedding``,
    most similar first."""
    settings = get_settings()
    base_query = (
        select(OwnPost, ContentAnalysis)
        .join(ContentAnalysis, ContentAnalysis.own_post_id == OwnPost.id)
        .options(selectinload(OwnPost.source_video))
        .where(ContentAnalysis.embedding.is_not(None))
    )

    if not settings.is_sqlite:
        result = await session.execute(
            base_query.order_by(ContentAnalysis.embedding.op("<=>")(query_embedding)).limit(limit)
        )
        return [
            (post, analysis, cosine_similarity(query_embedding, analysis.embedding or []))
            for post, analysis in result.all()
        ]

    result = await session.execute(base_query)
    scored = [
        (post, analysis, cosine_similarity(query_embedding, analysis.embedding or []))
        for post, analysis in result.all()
    ]
    scored.sort(key=lambda row: row[2], reverse=True)
    return scored[:limit]
