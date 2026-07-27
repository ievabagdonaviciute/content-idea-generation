"""Real meme templates + captioning via the official Imgflip API. See
docs/MEDIA_SOURCING.md for how to get a (free) Imgflip account -- captioning is
authenticated with real account credentials, not a separate API key, unlike every
other integration in this codebase. Never scrapes -- one documented endpoint for
listing templates, one for captioning.
"""

from __future__ import annotations

import httpx

from app.core.config import Settings
from app.integrations.media.base import MemeResult, MemeTemplate

IMGFLIP_API_BASE_URL = "https://api.imgflip.com"


class ImgflipError(RuntimeError):
    pass


class ImgflipMemeProvider:
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient | None = None) -> None:
        self._username = settings.imgflip_username or ""
        self._password = settings.imgflip_password or ""
        self._client = http_client or httpx.AsyncClient(
            base_url=IMGFLIP_API_BASE_URL, timeout=settings.http_timeout_seconds
        )
        self._owns_client = http_client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def list_templates(self, count: int) -> list[MemeTemplate]:
        response = await self._client.get("/get_memes")
        response.raise_for_status()
        body = response.json()
        if not body.get("success"):
            raise ImgflipError(body.get("error_message", "get_memes failed"))
        memes = body["data"]["memes"][:count]
        return [
            MemeTemplate(template_id=str(m["id"]), name=m["name"], box_count=m["box_count"])
            for m in memes
        ]

    async def caption(self, template: MemeTemplate, lines: list[str]) -> MemeResult:
        data = {
            "template_id": template.template_id,
            "username": self._username,
            "password": self._password,
        }
        for i, line in enumerate(lines[: template.box_count]):
            data[f"boxes[{i}][text]"] = line
        response = await self._client.post("/caption_image", data=data)
        response.raise_for_status()
        body = response.json()
        if not body.get("success"):
            raise ImgflipError(body.get("error_message", "caption_image failed"))
        return MemeResult(
            url=body["data"]["url"], template_name=template.name, caption_lines=lines
        )
