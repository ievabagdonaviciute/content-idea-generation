"""Structured AI-output schema for meme caption sets generated for one
ContentIdea. Validated via app/ai/json_generation.py before use, same as
ContentAnalysisSchema/ContentIdeaSchema -- see docs/MEDIA_SOURCING.md. Captions
are template-agnostic (short setup/punchline pairs) rather than shaped for one
specific meme format, since the templates themselves are picked separately from
Imgflip's most-popular list.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MemeCaptionSchema(BaseModel):
    lines: list[str] = Field(min_length=1, max_length=4)


class MemeCaptionsSchema(BaseModel):
    captions: list[MemeCaptionSchema] = Field(min_length=1)
