from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceVideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_video_id: str
    permalink: str
    caption: str | None
    posted_at: datetime | None
    duration_seconds: int | None
    stats: dict | None


class ContentAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    primary_topic: str
    secondary_topics: list[str]
    content_format: str
    presentation_style: list[str]
    hook_text: str
    hook_type: str
    hook_mechanism: str
    tone: list[str]
    story_structure: list[str]
    audience_promise: str
    emotional_angle: str | None
    cta_pattern: str | None
    editing_intensity: str
    estimated_pacing: str
    personal_story_level: float
    educational_level: float
    visual_analysis_available: bool
    transcript_available: bool
    confidence: float


class OwnPostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    processing_status: str
    processing_error: str | None
    source_video: SourceVideoOut
    content_analysis: ContentAnalysisOut | None
    created_at: datetime
