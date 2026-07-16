"""TikTok URL validation and normalization.

Used both by the Notion sync pipeline (validating saved links) and the inspiration
content resolver (guarding against SSRF by only ever issuing requests to an
allow-listed set of hosts).
"""

from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

from app.core.config import get_settings


class InvalidTikTokUrlError(ValueError):
    pass


_VIDEO_ID_PATTERN = re.compile(r"/video/(\d+)")
_SHORT_HOST_PATTERN = re.compile(r"^(vm|vt)\.tiktok\.com$", re.I)


def _host_allowed(host: str) -> bool:
    host = host.lower()
    settings = get_settings()
    return any(
        host == allowed or host.endswith(f".{allowed}")
        for allowed in settings.allowed_inspiration_hosts
    )


def normalize_tiktok_url(raw_url: str) -> str:
    """Validate that ``raw_url`` points at an allow-listed TikTok host and return a
    canonical form (scheme + host + path, no tracking query string)."""
    raw_url = raw_url.strip()
    if not raw_url:
        raise InvalidTikTokUrlError("URL is empty")

    parsed = urlparse(raw_url)
    if parsed.scheme not in ("http", "https"):
        raise InvalidTikTokUrlError(f"Unsupported URL scheme: {parsed.scheme!r}")
    if not parsed.netloc:
        raise InvalidTikTokUrlError("URL has no host")
    if not _host_allowed(parsed.netloc):
        raise InvalidTikTokUrlError(f"Host not allowed: {parsed.netloc!r}")

    canonical = urlunparse(
        (parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip("/"), "", "", "")
    )
    return canonical


def extract_video_id(normalized_url: str) -> str | None:
    match = _VIDEO_ID_PATTERN.search(normalized_url)
    if match:
        return match.group(1)
    return None


def is_short_link(normalized_url: str) -> bool:
    host = urlparse(normalized_url).netloc.lower()
    return bool(_SHORT_HOST_PATTERN.match(host))
