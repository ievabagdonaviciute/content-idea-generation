"""Tiered inspiration-content resolver. See docs/TIKTOK_INTEGRATION.md.

Tier 1: TikTok's public oEmbed endpoint (title/author/thumbnail/embed HTML).
Tier 2: media the user has explicitly placed under MEDIA_STORAGE_PATH themselves --
        an authorized-access extension point, never a scraper.
Tier 3: metadata-only fallback -- always the result when Tiers 1/2 yield nothing.

Never attempts to bypass authentication, anti-bot protection, CAPTCHAs, rate limits,
request signatures, or any other access control, per product requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

import httpx

from app.core.config import Settings, get_settings
from app.core.url_validation import extract_video_id, normalize_tiktok_url

Availability = Literal["full_media", "transcript_only", "metadata_only", "unavailable"]

TIKTOK_OEMBED_URL = "https://www.tiktok.com/oembed"


@dataclass
class ResolvedInspirationContent:
    availability: Availability
    canonical_url: str
    video_id: str | None
    author_name: str | None
    title: str | None
    thumbnail_url: str | None
    embed_html: str | None
    local_media_path: Path | None = None


class InspirationContentResolver(Protocol):
    async def resolve(self, url: str) -> ResolvedInspirationContent: ...


class AuthorizedMediaResolver:
    """Tier 2: looks for media the user has explicitly placed under
    ``MEDIA_STORAGE_PATH/authorized/{video_id}.mp4``. This is the documented,
    honest implementation of "optional, permitted media access" -- it reads a file
    you put there yourself. It does not fetch anything from TikTok."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def find_local_media(self, video_id: str | None) -> Path | None:
        if not video_id:
            return None
        candidate = self._settings.media_storage_dir / "authorized" / f"{video_id}.mp4"
        return candidate if candidate.is_file() else None


class TikTokOEmbedResolver:
    """Tier 1 (oEmbed) + Tier 2 (authorized local media) + Tier 3 (fallback),
    composed into the single ``InspirationContentResolver`` entry point."""

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        authorized_resolver: AuthorizedMediaResolver | None = None,
    ) -> None:
        settings = get_settings()
        self._client = http_client or httpx.AsyncClient(timeout=settings.http_timeout_seconds)
        self._owns_client = http_client is None
        self._authorized = authorized_resolver or AuthorizedMediaResolver(settings)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def resolve(self, url: str) -> ResolvedInspirationContent:
        canonical_url = normalize_tiktok_url(url)
        video_id = extract_video_id(canonical_url)

        author_name: str | None = None
        title: str | None = None
        thumbnail_url: str | None = None
        embed_html: str | None = None
        tier1_ok = False

        try:
            response = await self._client.get(TIKTOK_OEMBED_URL, params={"url": canonical_url})
            if response.status_code == 200:
                data = response.json()
                author_name = data.get("author_name")
                title = data.get("title")
                thumbnail_url = data.get("thumbnail_url")
                embed_html = data.get("html")
                tier1_ok = True
        except httpx.HTTPError:
            tier1_ok = False

        local_media_path = self._authorized.find_local_media(video_id)

        if local_media_path is not None:
            availability: Availability = "full_media"
        elif tier1_ok:
            availability = "metadata_only"
        else:
            availability = "unavailable"

        return ResolvedInspirationContent(
            availability=availability,
            canonical_url=canonical_url,
            video_id=video_id,
            author_name=author_name,
            title=title,
            thumbnail_url=thumbnail_url,
            embed_html=embed_html,
            local_media_path=local_media_path,
        )


class MockInspirationResolver:
    """Deterministic resolver for local dev/demo/tests, driven by the
    ``mock_availability`` hint in fixtures/notion_items.json so the seeded data
    demonstrates all four availability states without any network access."""

    def __init__(self, availability_by_url: dict[str, str] | None = None) -> None:
        self._availability_by_url = availability_by_url or {}

    async def resolve(self, url: str) -> ResolvedInspirationContent:
        canonical_url = normalize_tiktok_url(url)
        video_id = extract_video_id(canonical_url)
        availability: Availability = self._availability_by_url.get(canonical_url, "metadata_only")  # type: ignore[assignment]

        if availability == "unavailable":
            return ResolvedInspirationContent(
                availability="unavailable",
                canonical_url=canonical_url,
                video_id=video_id,
                author_name=None,
                title=None,
                thumbnail_url=None,
                embed_html=None,
            )

        return ResolvedInspirationContent(
            availability=availability,
            canonical_url=canonical_url,
            video_id=video_id,
            author_name="mock_creator",
            title="Mock inspiration video title",
            thumbnail_url="https://example.com/thumbnails/mock.jpg",
            embed_html=f'<blockquote class="tiktok-embed" cite="{canonical_url}"></blockquote>',
        )
