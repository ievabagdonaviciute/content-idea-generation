from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ContentProfileSnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sample_size: int
    content_pillars: list[dict]
    format_distribution: list[dict]
    underused_formats: list[str]
    typical_hooks: list[dict]
    typical_structures: list[dict]
    tone_distribution: list[dict]
    polished_vs_casual_ratio: float | None
    personal_story_frequency: float | None
    recently_overused_topics: list[str]
    recently_uncovered_topics: list[str]
    frequent_combinations: list[dict]
    content_gaps: list[str]
    observations_lt: list[str]
    confidence_notes: list[str]
    overall_confidence: float
    created_at: datetime
