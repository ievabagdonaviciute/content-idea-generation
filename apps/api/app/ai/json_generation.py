"""Validates every structured AI response before it is trusted, with a bounded
repair-retry loop. A malformed response is never persisted as a successful
analysis -- see docs/AI_PIPELINE.md."""

from __future__ import annotations

import json

from pydantic import BaseModel, ValidationError

from app.ai.base import TextGenerationProvider
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class JsonGenerationError(RuntimeError):
    def __init__(self, message: str, last_error: str) -> None:
        super().__init__(message)
        self.last_error = last_error


async def generate_validated_json[T: BaseModel](
    provider: TextGenerationProvider, prompt: str, schema: type[T]
) -> T:
    settings = get_settings()
    attempts = settings.ai_json_max_repair_attempts + 1
    last_error: str = ""
    current_prompt = prompt

    for attempt in range(1, attempts + 1):
        raw = await provider.generate_json(current_prompt, schema)
        try:
            data = json.loads(raw)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)
            logger.error(
                "ai_json_validation_failed",
                schema=schema.__name__,
                attempt=attempt,
                error=last_error,
            )
            current_prompt = (
                f"{prompt}\n\nThe previous response was invalid JSON for this schema. "
                f"Validation error: {last_error}\nReturn only corrected, valid JSON."
            )

    raise JsonGenerationError(
        f"Failed to obtain valid {schema.__name__} JSON after {attempts} attempts", last_error
    )
