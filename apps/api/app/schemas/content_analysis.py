"""Structured AI-output schema for a single post/inspiration-item analysis.

Mirrors the JSON shape in docs/PRODUCT_SPEC.md / docs/AI_PIPELINE.md. Used to
validate every ``TextGenerationProvider.generate_json`` response before anything is
persisted -- see ``app/ai/json_generation.py``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HookSchema(BaseModel):
    text: str
    type: str
    mechanism: str


class ContentAnalysisSchema(BaseModel):
    primary_topic: str
    secondary_topics: list[str] = Field(default_factory=list)
    content_format: str
    presentation_style: list[str] = Field(default_factory=list)
    hook: HookSchema
    tone: list[str] = Field(default_factory=list)
    story_structure: list[str] = Field(default_factory=list)
    audience_promise: str
    emotional_angle: str | None = None
    cta_pattern: str | None = None
    editing_intensity: Literal["low", "medium", "high"]
    estimated_pacing: Literal["slow", "medium", "fast"]
    personal_story_level: float = Field(ge=0.0, le=1.0)
    educational_level: float = Field(ge=0.0, le=1.0)
    visual_analysis_available: bool
    transcript_available: bool
    confidence: float = Field(ge=0.0, le=1.0)
