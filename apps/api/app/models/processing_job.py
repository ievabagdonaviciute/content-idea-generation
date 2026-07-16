from __future__ import annotations

import uuid

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

JOB_STATUSES = ("pending", "processing", "completed", "failed")
JOB_TYPES = (
    "analyze_own_post",
    "analyze_inspiration_item",
    "rebuild_profile",
    "generate_ideas",
    "sync_notion",
    "sync_tiktok",
)


class ProcessingJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Database-backed stand-in for a worker queue.

    A real async worker could later be added by having it claim rows where
    ``status = 'pending'`` instead of the current synchronous in-process execution
    -- see docs/ARCHITECTURE.md.
    """

    __tablename__ = "processing_jobs"

    job_type: Mapped[str] = mapped_column(String(48), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_entity_type: Mapped[str | None] = mapped_column(String(48), nullable=True)
    related_entity_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
