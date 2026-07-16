"""Picks fake or real AI providers based on whether AI_API_KEY is configured.
Everything downstream depends on the Protocols in app/ai/base.py, never on these
concrete classes directly."""

from __future__ import annotations

from functools import lru_cache

from app.ai.base import (
    EmbeddingProvider,
    TextGenerationProvider,
    TranscriptionProvider,
    VisionAnalysisProvider,
)
from app.ai.fake_providers import (
    FakeEmbeddingProvider,
    FakeTextGenerationProvider,
    FakeTranscriptionProvider,
    FakeVisionAnalysisProvider,
)
from app.ai.openai_compatible import OpenAICompatibleProvider
from app.core.config import get_settings


@lru_cache
def _real_provider() -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(get_settings())


def get_text_provider() -> TextGenerationProvider:
    return _real_provider() if get_settings().ai_api_key else FakeTextGenerationProvider()


def get_embedding_provider() -> EmbeddingProvider:
    return _real_provider() if get_settings().ai_api_key else FakeEmbeddingProvider()


def get_transcription_provider() -> TranscriptionProvider:
    return _real_provider() if get_settings().ai_api_key else FakeTranscriptionProvider()


def get_vision_provider() -> VisionAnalysisProvider:
    return _real_provider() if get_settings().ai_api_key else FakeVisionAnalysisProvider()
