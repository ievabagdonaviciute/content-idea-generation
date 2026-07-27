from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ContentIdeaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    concept: str
    content_pillar: str
    recommended_format: str
    format_label_lt: str
    why_it_fits_me: str
    inspiration_pattern: str | None
    originality_note: str | None
    closest_existing_post_id: uuid.UUID | None
    similarity_score: float
    similarity_category: str
    novelty_level: str
    hook_options: list[str]
    outline: list[str]
    suggested_duration_seconds: int
    production_effort: str
    output_language: str
    status: str
    created_at: datetime


class GeneratedBriefOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    idea_id: uuid.UUID
    objective: str
    target_viewer: str
    promise: str
    recommended_format: str
    recommended_duration_seconds: int
    hook_choices: list[str]
    beats: list[dict]
    b_roll_suggestions: list[str]
    on_screen_text: list[str]
    editing_notes: list[str]
    closing_line: str
    call_to_action: str
    caption_options: list[str]
    hashtags: list[str]
    claims_to_verify: list[str]
    output_language: str


class GeneratedScriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    idea_id: uuid.UUID
    mode: str
    spoken_lines: list[str]
    editing_notes: list[str]
    estimated_duration_seconds: int
    placeholders: list[str]
    output_language: str


class ImageResultOut(BaseModel):
    url: str
    thumbnail_url: str
    source_url: str
    credit: str | None = None


class MemeResultOut(BaseModel):
    url: str
    template_name: str
    caption_lines: list[str]


class IdeaSourcedMediaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    idea_id: uuid.UUID
    images: list[ImageResultOut]
    memes: list[MemeResultOut]


class IdeaGenerateRequest(BaseModel):
    count: int = Field(default=3, ge=1, le=10)
    content_pillar: str | None = None
    recommended_format: str | None = None
    instructions: str | None = None
    excluded_subjects: list[str] = Field(default_factory=list)
    output_language: str | None = None


class IdeaFeedbackRequest(BaseModel):
    rating: str
    comment: str | None = None


class ScriptGenerateRequest(BaseModel):
    mode: str
