from __future__ import annotations

from sqlalchemy import JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ContentProfileSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A versioned, timestamped rebuild of the derived creator content profile.

    Each rebuild inserts a new row rather than overwriting the previous one, so
    profile history is preserved. ``app/services/profile.py`` reads the latest row.
    """

    __tablename__ = "content_profile_snapshots"

    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_pillars: Mapped[list[dict]] = mapped_column(JSON, default=list)
    format_distribution: Mapped[list[dict]] = mapped_column(JSON, default=list)
    underused_formats: Mapped[list[str]] = mapped_column(JSON, default=list)
    typical_hooks: Mapped[list[dict]] = mapped_column(JSON, default=list)
    typical_structures: Mapped[list[dict]] = mapped_column(JSON, default=list)
    tone_distribution: Mapped[list[dict]] = mapped_column(JSON, default=list)
    polished_vs_casual_ratio: Mapped[float | None] = mapped_column(nullable=True)
    personal_story_frequency: Mapped[float | None] = mapped_column(nullable=True)
    recently_overused_topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    recently_uncovered_topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    frequent_combinations: Mapped[list[dict]] = mapped_column(JSON, default=list)
    content_gaps: Mapped[list[str]] = mapped_column(JSON, default=list)
    observations_lt: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence_notes: Mapped[list[str]] = mapped_column(JSON, default=list)
    overall_confidence: Mapped[float] = mapped_column(nullable=False)
