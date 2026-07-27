from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.content_analysis import ContentAnalysis

NOTION_STATUSES = ("New", "Processing", "Processed", "Failed")
AVAILABILITY_STATUSES = ("full_media", "transcript_only", "metadata_only", "unavailable")


class InspirationItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One row per Notion "TikTok Inspiration" database entry.

    Field names below follow the auto-provisioned Notion schema (see
    docs/NOTION_SETUP.md): Title, TikTok URL, Status, Added, Creator, Topic,
    Format, Why I saved it, My favorite part, Processing Error, Processed At.
    """

    __tablename__ = "inspiration_items"

    notion_page_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tiktok_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    tiktok_video_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    creator_name: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # User-supplied hints from Notion (optional) -- also back-filled by Kadro after
    # analysis when the user left them blank, so the Notion row stays useful as a
    # readable summary without ever overwriting something the user wrote.
    topics: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    format_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)

    note_why_saved: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    note_favorite_part: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    notion_status: Mapped[str] = mapped_column(String(16), default="New")
    availability: Mapped[str | None] = mapped_column(String(24), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    embed_html: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    source_date: Mapped[datetime | None] = mapped_column(nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    sync_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Set by the user via the "Mark as used" action once they've actually made a
    # video from this inspiration -- excludes it from future idea-generation
    # retrieval context (see app/services/idea_generation.py) without deleting it
    # or touching notion_status, which is reserved for sync-pipeline state.
    already_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    content_analysis: Mapped[ContentAnalysis | None] = relationship(
        back_populates="inspiration_item", uselist=False, cascade="all, delete-orphan"
    )
