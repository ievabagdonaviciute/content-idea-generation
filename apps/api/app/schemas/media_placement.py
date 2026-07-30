"""Structured AI-output schema for planning where sourced images/memes belong in
a finalized brief -- see docs/MEDIA_SOURCING.md. Each placement names a specific
beat/moment in the brief (e.g. "the beat that mentions superintelligence") rather
than being a generic, unplaced image, so the creator knows exactly where to drop
it while editing.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ImagePlacementSchema(BaseModel):
    placement: str
    search_query: str


class MemePlacementSchema(BaseModel):
    placement: str
    caption_lines: list[str] = Field(min_length=1, max_length=4)


class MediaPlacementPlanSchema(BaseModel):
    image_placements: list[ImagePlacementSchema] = Field(min_length=1)
    meme_placements: list[MemePlacementSchema] = Field(min_length=1)
