from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ContentFormat(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Reference table of recognized content formats.

    Deliberately a data table, not a Python enum, so new formats can be added by
    inserting a row instead of a schema migration touching every referencing table.
    See docs/PRODUCT_SPEC.md.
    """

    __tablename__ = "content_formats"

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    label_en: Mapped[str] = mapped_column(String(128), nullable=False)
    label_lt: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
