from __future__ import annotations

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserSettings(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Single-row settings table for this personal, single-user install."""

    __tablename__ = "user_settings"

    tiktok_username: Mapped[str] = mapped_column(String(64), nullable=False)
    default_output_language: Mapped[str] = mapped_column(String(8), default="lt")

    idea_mix_aligned_ratio: Mapped[float] = mapped_column(Float, default=0.6)
    idea_mix_stretch_ratio: Mapped[float] = mapped_column(Float, default=0.25)
    idea_mix_experimental_ratio: Mapped[float] = mapped_column(Float, default=0.15)

    similarity_too_similar_threshold: Mapped[float] = mapped_column(Float, default=0.9)
    similarity_related_threshold: Mapped[float] = mapped_column(Float, default=0.72)

    ai_text_model: Mapped[str] = mapped_column(String(128), default="gpt-4o-mini")
    ai_vision_model: Mapped[str] = mapped_column(String(128), default="gpt-4o-mini")
    ai_transcription_model: Mapped[str] = mapped_column(String(128), default="whisper-1")
    ai_embedding_model: Mapped[str] = mapped_column(
        String(128), default="text-embedding-3-small"
    )

    notion_sync_enabled: Mapped[bool] = mapped_column(default=False)
    notion_sync_interval_minutes: Mapped[int] = mapped_column(default=30)
    # Auto-discovered/auto-provisioned by NotionDatabaseProvisioner on first sync.
    # Never entered manually -- see docs/NOTION_SETUP.md.
    notion_database_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"UserSettings(id={self.id}, tiktok_username={self.tiktok_username!r})"
