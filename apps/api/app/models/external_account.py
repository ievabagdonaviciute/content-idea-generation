from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.creator_profile import CreatorProfile


class ExternalAccount(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An OAuth-connected external account (currently only ``tiktok``).

    Token material is stored here but is never included in any Pydantic response
    schema -- see docs/PRIVACY_AND_SECURITY.md.
    """

    __tablename__ = "external_accounts"

    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    external_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    access_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    scope: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    last_error: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    creator_profile: Mapped[CreatorProfile | None] = relationship(
        back_populates="external_account", uselist=False
    )
