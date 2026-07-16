from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.external_account import ExternalAccount


class CreatorProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "creator_profiles"

    external_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("external_accounts.id"), unique=True, nullable=False
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    follower_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    external_account: Mapped[ExternalAccount] = relationship(
        back_populates="creator_profile"
    )
