from __future__ import annotations

from app.core.config import get_settings
from app.integrations.media.base import ImageSearchProvider, MemeProvider
from app.integrations.media.fake import FakeImageSearchProvider, FakeMemeProvider
from app.integrations.media.imgflip import ImgflipMemeProvider
from app.integrations.media.pexels import PexelsImageProvider


def get_image_provider() -> ImageSearchProvider:
    settings = get_settings()
    if settings.use_mock_images:
        return FakeImageSearchProvider()
    return PexelsImageProvider(settings)


def get_meme_provider() -> MemeProvider:
    settings = get_settings()
    if settings.use_mock_memes:
        return FakeMemeProvider()
    return ImgflipMemeProvider(settings)
