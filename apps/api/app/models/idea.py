from __future__ import annotations

import uuid

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import Vector

IDEA_STATUSES = ("proposed", "saved", "done", "archived")
NOVELTY_LEVELS = ("aligned", "stretch", "experimental")
SIMILARITY_CATEGORIES = ("new", "related_but_distinct", "follow_up", "too_similar")
IDEA_SOURCE_ROLES = ("identity_reference", "inspiration_reference", "similarity_neighbor")
FEEDBACK_RATINGS = ("love", "maybe", "not_for_me", "already_covered")


class ContentIdea(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "content_ideas"

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    concept: Mapped[str] = mapped_column(Text, nullable=False)
    content_pillar: Mapped[str] = mapped_column(String(128), nullable=False)
    recommended_format: Mapped[str] = mapped_column(
        ForeignKey("content_formats.code"), nullable=False
    )
    format_label_lt: Mapped[str] = mapped_column(String(128), nullable=False)
    why_it_fits_me: Mapped[str] = mapped_column(Text, nullable=False)
    inspiration_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    originality_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    closest_existing_post_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("own_posts.id"), nullable=True
    )
    similarity_score: Mapped[float] = mapped_column(Float, default=0.0)
    similarity_category: Mapped[str] = mapped_column(String(24), default="new")
    novelty_level: Mapped[str] = mapped_column(String(16), nullable=False)
    hook_options: Mapped[list[str]] = mapped_column(JSON, default=list)
    outline: Mapped[list[str]] = mapped_column(JSON, default=list)
    suggested_duration_seconds: Mapped[int] = mapped_column(Integer, default=60)
    production_effort: Mapped[str] = mapped_column(String(16), default="medium")
    output_language: Mapped[str] = mapped_column(String(8), default="lt")
    status: Mapped[str] = mapped_column(String(16), default="proposed")
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(get_settings().ai_embedding_dimensions), nullable=True
    )

    sources: Mapped[list[IdeaSource]] = relationship(
        back_populates="idea", cascade="all, delete-orphan"
    )
    feedback_entries: Mapped[list[IdeaFeedback]] = relationship(
        back_populates="idea", cascade="all, delete-orphan"
    )
    brief: Mapped[GeneratedBrief | None] = relationship(
        back_populates="idea", uselist=False, cascade="all, delete-orphan"
    )
    script: Mapped[GeneratedScript | None] = relationship(
        back_populates="idea", uselist=False, cascade="all, delete-orphan"
    )
    sourced_media: Mapped[IdeaSourcedMedia | None] = relationship(
        back_populates="idea", uselist=False, cascade="all, delete-orphan"
    )


class IdeaSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Links a ContentIdea to the OwnPost/InspirationItem retrieved as context for
    it, so idea generation is auditable rather than an opaque black box."""

    __tablename__ = "idea_sources"

    idea_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("content_ideas.id"), nullable=False)
    own_post_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("own_posts.id"), nullable=True
    )
    inspiration_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("inspiration_items.id"), nullable=True
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)

    idea: Mapped[ContentIdea] = relationship(back_populates="sources")


class IdeaFeedback(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "idea_feedback"

    idea_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("content_ideas.id"), nullable=False)
    rating: Mapped[str] = mapped_column(String(24), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    idea: Mapped[ContentIdea] = relationship(back_populates="feedback_entries")


class GeneratedBrief(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "generated_briefs"

    idea_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_ideas.id"), unique=True, nullable=False
    )
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    target_viewer: Mapped[str] = mapped_column(Text, nullable=False)
    promise: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_format: Mapped[str] = mapped_column(String(64), nullable=False)
    recommended_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    hook_choices: Mapped[list[str]] = mapped_column(JSON, default=list)
    beats: Mapped[list[dict]] = mapped_column(JSON, default=list)
    b_roll_suggestions: Mapped[list[str]] = mapped_column(JSON, default=list)
    on_screen_text: Mapped[list[str]] = mapped_column(JSON, default=list)
    editing_notes: Mapped[list[str]] = mapped_column(JSON, default=list)
    closing_line: Mapped[str] = mapped_column(Text, nullable=False)
    call_to_action: Mapped[str] = mapped_column(Text, nullable=False)
    caption_options: Mapped[list[str]] = mapped_column(JSON, default=list)
    hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)
    claims_to_verify: Mapped[list[str]] = mapped_column(JSON, default=list)
    output_language: Mapped[str] = mapped_column(String(8), default="lt")

    idea: Mapped[ContentIdea] = relationship(back_populates="brief")


class GeneratedScript(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "generated_scripts"

    idea_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_ideas.id"), unique=True, nullable=False
    )
    mode: Mapped[str] = mapped_column(String(48), nullable=False)
    spoken_lines: Mapped[list[str]] = mapped_column(JSON, default=list)
    editing_notes: Mapped[list[str]] = mapped_column(JSON, default=list)
    estimated_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    placeholders: Mapped[list[str]] = mapped_column(JSON, default=list)
    output_language: Mapped[str] = mapped_column(String(8), default="lt")

    idea: Mapped[ContentIdea] = relationship(back_populates="script")


class IdeaSourcedMedia(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Images and captioned memes sourced for one ContentIdea, so a creator can
    pull production-ready visuals for editing without leaving Kadro. See
    docs/MEDIA_SOURCING.md. ``images``/``memes`` are lists of plain dicts
    (ImageResult/MemeResult, dataclasses.asdict'd) rather than a normalized table,
    since they're read-only display data, never queried by field."""

    __tablename__ = "idea_sourced_media"

    idea_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_ideas.id"), unique=True, nullable=False
    )
    images: Mapped[list[dict]] = mapped_column(JSON, default=list)
    memes: Mapped[list[dict]] = mapped_column(JSON, default=list)

    idea: Mapped[ContentIdea] = relationship(back_populates="sourced_media")
