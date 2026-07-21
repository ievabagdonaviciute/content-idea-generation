"""Structured AI-output schema for a production brief generated from a
ContentIdea. See docs/AI_PIPELINE.md "Briefs and scripts"."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BeatSchema(BaseModel):
    label: str
    description: str


class GeneratedBriefSchema(BaseModel):
    objective: str
    target_viewer: str
    promise: str
    recommended_format: str
    recommended_duration_seconds: int = Field(gt=0)
    hook_choices: list[str] = Field(min_length=1)
    beats: list[BeatSchema] = Field(min_length=1)
    b_roll_suggestions: list[str] = Field(default_factory=list)
    on_screen_text: list[str] = Field(default_factory=list)
    editing_notes: list[str] = Field(default_factory=list)
    closing_line: str
    call_to_action: str
    caption_options: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    claims_to_verify: list[str] = Field(default_factory=list)
