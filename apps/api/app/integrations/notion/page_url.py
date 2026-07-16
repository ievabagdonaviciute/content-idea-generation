"""Extracts a Notion page ID from the hardcoded NOTION_PAGE_URL.

Handles both the legacy ``notion.so/Some-Title-<32hex>`` link format and the
``app.notion.com/p/Some-Title-<32hex>`` format used by personal Notion links.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

_ID_PATTERN = re.compile(
    r"([0-9a-fA-F]{32}"
    r"|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)


class InvalidNotionPageUrlError(ValueError):
    pass


def extract_page_id(page_url: str) -> str:
    """Return a dash-formatted UUID string suitable for the Notion API."""
    parsed = urlparse(page_url)
    if "notion" not in parsed.netloc:
        raise InvalidNotionPageUrlError(f"Not a Notion URL: {page_url!r}")

    candidate = parsed.path.rsplit("/", 1)[-1]
    match = _ID_PATTERN.search(candidate)
    if not match:
        raise InvalidNotionPageUrlError(f"Could not find a page ID in URL: {page_url!r}")

    raw = match.group(1).replace("-", "")
    return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"
