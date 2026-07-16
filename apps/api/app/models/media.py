from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

MEDIA_KINDS = ("audio_extract", "video_source", "sampled_frame", "thumbnail")


class MediaAsset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "media_assets"

    own_post_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("own_posts.id"), nullable=True
    )
    inspiration_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("inspiration_items.id"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
