"""Structured AI-output schema for a spoken script generated from a ContentIdea
(and optionally its brief). ``mode`` is chosen by the caller and threaded into
the prompt, not asked of the model -- see docs/AI_PIPELINE.md "Briefs and
scripts". Spoken text and editing directions are kept in separate fields so the
spoken track never accidentally contains a bracketed instruction (see
docs/LITHUANIAN_GENERATION_GUIDE.md).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class GeneratedScriptSchema(BaseModel):
    spoken_lines: list[str] = Field(min_length=1)
    editing_notes: list[str] = Field(default_factory=list)
    estimated_duration_seconds: int = Field(gt=0)
    placeholders: list[str] = Field(default_factory=list)
