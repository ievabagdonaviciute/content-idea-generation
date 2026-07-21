"""Structured AI-output schema for one generated content idea. Validated via
app/ai/json_generation.py before persistence, same as ContentAnalysisSchema --
see docs/AI_PIPELINE.md "Idea generation". ``novelty_level`` is decided by
app/services/idea_generation.py before the prompt is built, not asked of the
model, so it is not part of this schema.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ContentIdeaSchema(BaseModel):
    title: str
    concept: str
    content_pillar: str
    recommended_format: str
    format_label_lt: str
    why_it_fits_me: str
    inspiration_pattern: str | None = None
    originality_note: str | None = None
    hook_options: list[str] = Field(min_length=3)
    outline: list[str] = Field(default_factory=list)
    suggested_duration_seconds: int = Field(gt=0)
    production_effort: Literal["low", "medium", "high"] = "medium"
