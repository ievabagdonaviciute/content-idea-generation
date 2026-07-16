from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.own_post import OwnPost


class SourceVideo(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A raw video synced from the creator's own TikTok account, before/alongside
    analysis. See ``OwnPost`` for the analyzed, profile-facing representation."""

    __tablename__ = "source_videos"

    creator_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("creator_profiles.id"), nullable=False
    )
    external_video_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    permalink: Mapped[str] = mapped_column(String(1024), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sync_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sync_runs.id"), nullable=True
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(nullable=True)

    own_post: Mapped[OwnPost | None] = relationship(
        back_populates="source_video", uselist=False
    )
