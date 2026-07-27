"""Real image search via the official Pexels API. See docs/MEDIA_SOURCING.md for
how to get a free API key. Never scrapes -- one documented, licensed endpoint.
"""

from __future__ import annotations

import httpx

from app.core.config import Settings
from app.integrations.media.base import ImageResult

PEXELS_API_BASE_URL = "https://api.pexels.com/v1"


class PexelsImageProvider:
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient | None = None) -> None:
        self._client = http_client or httpx.AsyncClient(
            base_url=PEXELS_API_BASE_URL,
            headers={"Authorization": settings.pexels_api_key or ""},
            timeout=settings.http_timeout_seconds,
        )
        self._owns_client = http_client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def search(self, query: str, count: int) -> list[ImageResult]:
        response = await self._client.get(
            "/search", params={"query": query, "per_page": count}
        )
        response.raise_for_status()
        photos = response.json().get("photos", [])
        return [
            ImageResult(
                url=photo["src"]["large"],
                thumbnail_url=photo["src"]["medium"],
                source_url=photo["url"],
                credit=f"Photo by {photo['photographer']} on Pexels",
            )
            for photo in photos
        ]
