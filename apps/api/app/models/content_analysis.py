from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, CheckConstraint, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import Vector

if TYPE_CHECKING:
    from app.models.inspiration import InspirationItem
    from app.models.own_post import OwnPost

EDITING_INTENSITIES = ("low", "medium", "high")
PACING_VALUES = ("slow", "medium", "fast")


class ContentAnalysis(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Structured analysis for exactly one of an OwnPost or an InspirationItem.

    Mirrors the JSON shape in docs/PRODUCT_SPEC.md / docs/AI_PIPELINE.md. The
    emotional_angle/cta_pattern fields additionally cover the inspiration-specific
    dimensions called out in docs/PRODUCT_SPEC.md ("Important product principle").
    """

    __tablename__ = "content_analyses"
    __table_args__ = (
        CheckConstraint(
            "(own_post_id IS NOT NULL) != (inspiration_item_id IS NOT NULL)",
            name="content_analysis_exactly_one_owner",
        ),
    )

    own_post_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("own_posts.id"), nullable=True, unique=True
    )
    inspiration_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("inspiration_items.id"), nullable=True, unique=True
    )

    primary_topic: Mapped[str] = mapped_column(String(256), nullable=False)
    secondary_topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    content_format: Mapped[str] = mapped_column(
        ForeignKey("content_formats.code"), nullable=False
    )
    presentation_style: Mapped[list[str]] = mapped_column(JSON, default=list)

    hook_text: Mapped[str] = mapped_column(String(512), nullable=False)
    hook_type: Mapped[str] = mapped_column(String(64), nullable=False)
    hook_mechanism: Mapped[str] = mapped_column(String(256), nullable=False)

    tone: Mapped[list[str]] = mapped_column(JSON, default=list)
    story_structure: Mapped[list[str]] = mapped_column(JSON, default=list)
    audience_promise: Mapped[str] = mapped_column(String(512), nullable=False)
    emotional_angle: Mapped[str | None] = mapped_column(String(256), nullable=True)
    cta_pattern: Mapped[str | None] = mapped_column(String(256), nullable=True)

    editing_intensity: Mapped[str] = mapped_column(String(16), nullable=False)
    estimated_pacing: Mapped[str] = mapped_column(String(16), nullable=False)
    personal_story_level: Mapped[float] = mapped_column(Float, nullable=False)
    educational_level: Mapped[float] = mapped_column(Float, nullable=False)

    visual_analysis_available: Mapped[bool] = mapped_column(Boolean, default=False)
    transcript_available: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(get_settings().ai_embedding_dimensions), nullable=True
    )

    own_post: Mapped[OwnPost | None] = relationship(back_populates="content_analysis")
    inspiration_item: Mapped[InspirationItem | None] = relationship(
        back_populates="content_analysis"
    )
