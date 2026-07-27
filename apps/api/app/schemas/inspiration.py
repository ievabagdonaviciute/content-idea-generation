from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InspirationItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    notion_page_id: str
    title: str | None
    tiktok_url: str
    tiktok_video_id: str | None
    creator_name: str | None
    topics: list[str] | None
    format_hint: str | None
    note_why_saved: str | None
    note_favorite_part: str | None
    notion_status: str
    availability: str | None
    thumbnail_url: str | None
    embed_html: str | None
    processed_at: datetime | None
    error_message: str | None
    already_used: bool
    created_at: datetime


class SyncRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    items_processed: int
    items_failed: int
    error_summary: str | None
