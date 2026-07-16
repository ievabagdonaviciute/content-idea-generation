"""AI provider interfaces. Domain code depends only on these Protocols -- never on
an SDK or a model name literal. See docs/AI_PIPELINE.md."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel


@dataclass
class TranscriptionResult:
    text: str
    language_detected: str  # "lt" | "en" | "mixed" | "unknown"


@dataclass
class VisualDescription:
    frame_descriptions: list[str] = field(default_factory=list)
    dominant_style: str | None = None


class TranscriptionProvider(Protocol):
    async def transcribe(self, audio_path: Path) -> TranscriptionResult: ...


class VisionAnalysisProvider(Protocol):
    async def describe_frames(self, frame_paths: list[Path]) -> VisualDescription: ...


class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class TextGenerationProvider(Protocol):
    async def generate_json(self, prompt: str, schema: type[BaseModel]) -> str:
        """Return raw JSON text matching ``schema`` as closely as the model can
        manage. Validation and repair-retry live in ``app/ai/json_generation.py`` --
        providers are not responsible for guaranteeing valid JSON."""
        ...
