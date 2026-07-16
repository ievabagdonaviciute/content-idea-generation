from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.content_analysis import ContentAnalysis
    from app.models.source_video import SourceVideo

PROCESSING_STATUSES = ("pending", "processing", "completed", "failed")


class OwnPost(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "own_posts"

    source_video_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_videos.id"), unique=True, nullable=False
    )
    processing_status: Mapped[str] = mapped_column(String(16), default="pending")
    processing_error: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    source_video: Mapped[SourceVideo] = relationship(back_populates="own_post")
    content_analysis: Mapped[ContentAnalysis | None] = relationship(
        back_populates="own_post", uselist=False, cascade="all, delete-orphan"
    )
