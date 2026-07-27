"""Sets InspirationItem.already_used and mirrors it to the real Notion row.
Shared by the direct "mark as used" action (app/api/v1/inspiration.py) and by
marking a ContentIdea "done" (app/api/v1/ideas.py), which auto-marks every
inspiration item that fed into that idea -- see docs/DATA_MODEL.md.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.integrations.notion.factory import get_notion_client
from app.models.inspiration import InspirationItem

logger = get_logger(__name__)


async def set_inspiration_used(item: InspirationItem, value: bool) -> None:
    item.already_used = value
    try:
        await get_notion_client().update_row(
            item.notion_page_id, status=item.notion_status, already_used=value
        )
    except Exception as exc:  # noqa: BLE001 -- a Notion write-back failure must not
        # block the local state change the caller asked for; it just won't be
        # reflected on the Notion side until the next successful write.
        logger.error(
            "notion_already_used_writeback_failed", item_id=str(item.id), error=str(exc)
        )
