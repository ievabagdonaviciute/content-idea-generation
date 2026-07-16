from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

LANGUAGES_DETECTED = ("lt", "en", "mixed", "unknown")


class Transcript(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "transcripts"

    own_post_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("own_posts.id"), nullable=True, unique=True
    )
    inspiration_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("inspiration_items.id"), nullable=True, unique=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    language_detected: Mapped[str] = mapped_column(String(16), default="unknown")
    is_original_language: Mapped[bool] = mapped_column(Boolean, default=True)
