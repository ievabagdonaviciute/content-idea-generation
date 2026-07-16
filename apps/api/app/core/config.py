"""Central application configuration.

The temporary project name lives in exactly one place: ``project_name`` below.
Renaming the product means editing that one default (and the mirrored constant in
``apps/web/lib/config.ts``).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.personal_config import DEFAULT_TIKTOK_USERNAME


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    project_name: str = "Kadro"
    app_env: str = Field(default="development", alias="APP_ENV")

    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/kadro.db",
        alias="DATABASE_URL",
    )
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    backend_url: str = Field(default="http://localhost:8000", alias="BACKEND_URL")

    default_tiktok_username: str = Field(
        default=DEFAULT_TIKTOK_USERNAME, alias="DEFAULT_TIKTOK_USERNAME"
    )
    default_output_language: str = Field(default="lt", alias="DEFAULT_OUTPUT_LANGUAGE")

    # The only Notion-related environment variable: a credential, not a stable
    # config value. The target page/database are hardcoded in personal_config.py
    # and auto-discovered/auto-provisioned -- see docs/NOTION_SETUP.md.
    notion_token: str | None = Field(default=None, alias="NOTION_TOKEN")
    notion_sync_enabled: bool = Field(default=False, alias="NOTION_SYNC_ENABLED")
    notion_sync_interval_minutes: int = Field(
        default=30, alias="NOTION_SYNC_INTERVAL_MINUTES"
    )

    tiktok_client_key: str | None = Field(default=None, alias="TIKTOK_CLIENT_KEY")
    tiktok_client_secret: str | None = Field(default=None, alias="TIKTOK_CLIENT_SECRET")
    tiktok_redirect_uri: str | None = Field(default=None, alias="TIKTOK_REDIRECT_URI")

    ai_api_key: str | None = Field(default=None, alias="AI_API_KEY")
    ai_base_url: str = Field(default="https://api.openai.com/v1", alias="AI_BASE_URL")
    ai_text_model: str = Field(default="gpt-4o-mini", alias="AI_TEXT_MODEL")
    ai_vision_model: str = Field(default="gpt-4o-mini", alias="AI_VISION_MODEL")
    ai_transcription_model: str = Field(default="whisper-1", alias="AI_TRANSCRIPTION_MODEL")
    ai_embedding_model: str = Field(
        default="text-embedding-3-small", alias="AI_EMBEDDING_MODEL"
    )
    ai_embedding_dimensions: int = Field(default=256, alias="AI_EMBEDDING_DIMENSIONS")
    ai_json_max_repair_attempts: int = Field(
        default=2, alias="AI_JSON_MAX_REPAIR_ATTEMPTS"
    )

    max_media_size_mb: int = Field(default=200, alias="MAX_MEDIA_SIZE_MB")
    media_storage_path: str = Field(default="./data/media", alias="MEDIA_STORAGE_PATH")

    http_timeout_seconds: float = Field(default=15.0, alias="HTTP_TIMEOUT_SECONDS")
    allowed_inspiration_hosts: tuple[str, ...] = (
        "tiktok.com",
        "www.tiktok.com",
        "vm.tiktok.com",
        "m.tiktok.com",
    )

    idea_mix_aligned_ratio: float = Field(default=0.6, alias="IDEA_MIX_ALIGNED_RATIO")
    idea_mix_stretch_ratio: float = Field(default=0.25, alias="IDEA_MIX_STRETCH_RATIO")
    idea_mix_experimental_ratio: float = Field(
        default=0.15, alias="IDEA_MIX_EXPERIMENTAL_RATIO"
    )
    similarity_too_similar_threshold: float = Field(
        default=0.9, alias="SIMILARITY_TOO_SIMILAR_THRESHOLD"
    )
    similarity_related_threshold: float = Field(
        default=0.72, alias="SIMILARITY_RELATED_THRESHOLD"
    )

    max_sample_frames: int = Field(default=6, alias="MAX_SAMPLE_FRAMES")

    @model_validator(mode="after")
    def _check_idea_mix(self) -> Settings:
        total = (
            self.idea_mix_aligned_ratio
            + self.idea_mix_stretch_ratio
            + self.idea_mix_experimental_ratio
        )
        if not (0.99 <= total <= 1.01):
            raise ValueError(
                "idea mix ratios must sum to 1.0, got "
                f"{self.idea_mix_aligned_ratio}+{self.idea_mix_stretch_ratio}"
                f"+{self.idea_mix_experimental_ratio}={total}"
            )
        return self

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def media_storage_dir(self) -> Path:
        path = Path(self.media_storage_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def use_mock_notion(self) -> bool:
        """True when no real Notion token is configured -- use fixture-backed data."""
        return not bool(self.notion_token)

    @property
    def use_mock_tiktok(self) -> bool:
        """True when TikTok Login Kit credentials are not fully configured."""
        return not (
            self.tiktok_client_key and self.tiktok_client_secret and self.tiktok_redirect_uri
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
