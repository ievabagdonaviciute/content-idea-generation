"""Production OwnContentProvider: TikTok Login Kit (OAuth) + Display API.

Implemented against TikTok's documented v2 Display API shape, but -- honestly --
unverified against a live TikTok app, since this MVP ships without approved TikTok
developer credentials. See docs/TIKTOK_INTEGRATION.md for exactly what is and is not
covered, and what you need to configure before this path is exercised for real.

This adapter never fabricates data: with no stored OAuth token it raises
``TikTokNotConfiguredError`` rather than returning an empty/fake profile, and a
401/expired-token response from TikTok is translated into ``TikTokAuthError`` so the
sync service can record a clean authorization failure instead of corrupting data.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from app.core.config import Settings
from app.integrations.tiktok.base import (
    CreatorProfileData,
    SourceVideoData,
    TikTokAuthError,
    TikTokNotConfiguredError,
)

DISPLAY_API_BASE_URL = "https://open.tiktokapis.com/v2"
USER_INFO_FIELDS = "open_id,username,display_name,avatar_url,bio_description,follower_count"
VIDEO_FIELDS = (
    "id,video_description,create_time,duration,cover_image_url,share_url,"
    "view_count,like_count,comment_count,share_count"
)


class TikTokLoginKitProvider:
    def __init__(
        self,
        settings: Settings,
        access_token: str | None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        has_credentials = (
            settings.tiktok_client_key
            and settings.tiktok_client_secret
            and settings.tiktok_redirect_uri
        )
        if not has_credentials:
            raise TikTokNotConfiguredError(
                "TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET and TIKTOK_REDIRECT_URI must all be "
                "set to use the production TikTok adapter. See docs/TIKTOK_INTEGRATION.md."
            )
        if not access_token:
            raise TikTokNotConfiguredError(
                "No stored TikTok OAuth token found. Complete the Login Kit authorization "
                "flow once before syncing. See docs/TIKTOK_INTEGRATION.md."
            )
        self._access_token = access_token
        self._client = http_client or httpx.AsyncClient(
            base_url=DISPLAY_API_BASE_URL, timeout=settings.http_timeout_seconds
        )
        self._owns_client = http_client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token}"}

    async def get_profile(self) -> CreatorProfileData:
        response = await self._client.get(
            "/user/info/", params={"fields": USER_INFO_FIELDS}, headers=self._headers()
        )
        self._raise_for_auth_errors(response)
        response.raise_for_status()
        user = response.json()["data"]["user"]
        return CreatorProfileData(
            username=user["username"],
            display_name=user.get("display_name"),
            avatar_url=user.get("avatar_url"),
            bio=user.get("bio_description"),
            follower_count=user.get("follower_count"),
        )

    async def list_videos(self) -> list[SourceVideoData]:
        videos: list[SourceVideoData] = []
        cursor: int | None = None
        has_more = True

        while has_more:
            body: dict[str, object] = {"max_count": 20}
            if cursor is not None:
                body["cursor"] = cursor
            response = await self._client.post(
                "/video/list/",
                params={"fields": VIDEO_FIELDS},
                json=body,
                headers=self._headers(),
            )
            self._raise_for_auth_errors(response)
            response.raise_for_status()
            data = response.json()["data"]
            for item in data.get("videos", []):
                videos.append(
                    SourceVideoData(
                        external_video_id=str(item["id"]),
                        permalink=item.get("share_url", ""),
                        caption=item.get("video_description"),
                        posted_at=datetime.fromtimestamp(item["create_time"], tz=UTC)
                        if item.get("create_time")
                        else None,
                        duration_seconds=item.get("duration"),
                        stats={
                            "views": item.get("view_count", 0),
                            "likes": item.get("like_count", 0),
                            "comments": item.get("comment_count", 0),
                            "shares": item.get("share_count", 0),
                        },
                    )
                )
            has_more = bool(data.get("has_more", False))
            cursor = data.get("cursor")

        return videos

    @staticmethod
    def _raise_for_auth_errors(response: httpx.Response) -> None:
        if response.status_code == 401:
            raise TikTokAuthError("TikTok authorization is invalid, expired, or revoked.")
        if response.status_code == 200:
            error = response.json().get("error", {})
            if error.get("code") in ("access_token_invalid", "access_token_expired"):
                raise TikTokAuthError(f"TikTok authorization error: {error}")
