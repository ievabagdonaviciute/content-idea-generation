"""A single OpenAI-compatible provider implementing all four AI protocols against
``AI_BASE_URL``/``AI_API_KEY``. Model names always come from settings -- never a
literal in this module. See docs/AI_PIPELINE.md.

This talks to a real HTTP API and is therefore never exercised in the test suite
(tests use the fake providers exclusively).
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx
from pydantic import BaseModel

from app.ai.base import TranscriptionResult, VisualDescription
from app.core.config import Settings


class OpenAICompatibleProvider:
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = http_client or httpx.AsyncClient(
            base_url=settings.ai_base_url,
            headers={"Authorization": f"Bearer {settings.ai_api_key}"},
            timeout=settings.http_timeout_seconds,
        )
        self._owns_client = http_client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def generate_json(self, prompt: str, schema: type[BaseModel]) -> str:
        # response_format: json_object only guarantees syntactically valid JSON, not
        # any particular shape -- the model never sees field names/types/enums unless
        # they're spelled out here, so without this it reliably guesses a plausible
        # but schema-mismatched shape (e.g. a flat string instead of a nested object).
        schema_instructions = (
            "Respond with a single JSON object that validates against exactly this "
            "JSON Schema. Use only these field names and types; respect every enum "
            "and numeric range. No extra commentary, no markdown fences.\n\n"
            f"{json.dumps(schema.model_json_schema())}"
        )
        response = await self._client.post(
            "/chat/completions",
            json={
                "model": self._settings.ai_text_model,
                "messages": [
                    {"role": "system", "content": schema_instructions},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"])

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.post(
            "/embeddings",
            json={"model": self._settings.ai_embedding_model, "input": texts},
        )
        response.raise_for_status()
        data = response.json()["data"]
        return [item["embedding"] for item in data]

    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        with audio_path.open("rb") as audio_file:
            response = await self._client.post(
                "/audio/transcriptions",
                data={"model": self._settings.ai_transcription_model},
                files={"file": (audio_path.name, audio_file, "audio/mpeg")},
            )
        response.raise_for_status()
        body = response.json()
        return TranscriptionResult(
            text=body.get("text", ""), language_detected=body.get("language", "unknown")
        )

    async def describe_frames(self, frame_paths: list[Path]) -> VisualDescription:
        content: list[dict] = [
            {"type": "text", "text": "Describe each frame briefly for content analysis."}
        ]
        for frame_path in frame_paths:
            encoded = base64.b64encode(frame_path.read_bytes()).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
                }
            )
        response = await self._client.post(
            "/chat/completions",
            json={
                "model": self._settings.ai_vision_model,
                "messages": [{"role": "user", "content": content}],
            },
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        return VisualDescription(frame_descriptions=[text], dominant_style=None)
