"""Deterministic fake AI providers used whenever ``AI_API_KEY`` is not configured,
and always in tests. No network access, ever. See docs/AI_PIPELINE.md.

Fakes are deterministic functions of their input so the same caption/prompt always
analyzes the same way -- useful for stable tests and a stable demo.
"""

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

from pydantic import BaseModel

from app.ai.base import TranscriptionResult, VisualDescription
from app.core.config import get_settings

_LT_TOPICS = [
    "dirbtinis intelektas",
    "programavimas",
    "universiteto gyvenimas",
    "technologijų naujienos",
    "duomenų bazės",
    "karjera IT srityje",
]
_LT_HOOKS = [
    ("Ar žinojai, kad {topic} veikia visai kitaip, nei atrodo?", "provocative_question"),
    ("Prieš savaitę man nutiko kažkas, kas pakeitė požiūrį į {topic}.", "personal_anecdote"),
    ("Trys dalykai apie {topic}, kuriuos supratau per vėlai.", "listicle_promise"),
    ("Visi klysta dėl {topic} -- štai kodėl.", "myth_bust"),
]
_FORMATS = [
    "edited_tech_explainer",
    "casual_talking_head",
    "grwm_story",
    "tech_news_recap",
    "screen_recording_demo",
    "myth_vs_fact",
]


def _seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def _pick(seed: int, options: list, salt: int = 0):
    return options[(seed + salt) % len(options)]


class FakeTranscriptionProvider:
    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        seed = _seed(str(audio_path))
        return TranscriptionResult(
            text="[fake transkripcija] Sveiki, šiandien kalbėsime apie technologijas.",
            language_detected=_pick(seed, ["lt", "en", "mixed"]),
        )


class FakeVisionAnalysisProvider:
    async def describe_frames(self, frame_paths: list[Path]) -> VisualDescription:
        seed = _seed("".join(str(p) for p in frame_paths)) if frame_paths else 0
        return VisualDescription(
            frame_descriptions=[f"[fake frame description {i}]" for i in range(len(frame_paths))],
            dominant_style=_pick(seed, ["studio_lighting", "handheld_casual", "screen_capture"]),
        )


class FakeEmbeddingProvider:
    """A deterministic bag-of-words hashing embedding. Not a real semantic model --
    but cosine similarity between two texts does reflect shared vocabulary, which is
    enough to exercise similarity search/dedup logic realistically offline."""

    _TOKEN_PATTERN = re.compile(r"[a-zA-ZąčęėįšųūžĄČĘĖĮŠŲŪŽ]+", re.UNICODE)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        dim = get_settings().ai_embedding_dimensions
        return [self._embed_one(text, dim) for text in texts]

    def _embed_one(self, text: str, dim: int) -> list[float]:
        vector = [0.0] * dim
        tokens = self._TOKEN_PATTERN.findall(text.lower())
        for token in tokens:
            bucket = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dim
            vector[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


class FakeTextGenerationProvider:
    """Produces schema-conforming Lithuanian (or English) placeholder JSON.

    Deterministic per (prompt, schema): registered builder functions keyed by
    schema class name, not generic reflection over arbitrary Pydantic models --
    the set of schemas this needs to support is small and known.
    """

    async def generate_json(self, prompt: str, schema: type[BaseModel]) -> str:
        builder = _BUILDERS.get(schema.__name__)
        if builder is None:
            raise NotImplementedError(
                f"FakeTextGenerationProvider has no builder registered for {schema.__name__}"
            )
        return builder(prompt)


def _is_english(prompt: str) -> bool:
    return "output_language: en" in prompt.lower()


def _build_content_analysis(prompt: str) -> str:
    import json

    seed = _seed(prompt)
    english = _is_english(prompt)
    topic = _pick(seed, _LT_TOPICS, salt=0)
    hook_template, hook_type = _pick(seed, _LT_HOOKS, salt=1)
    content_format = _pick(seed, _FORMATS, salt=2)

    if english:
        topic = {
            "dirbtinis intelektas": "artificial intelligence",
            "programavimas": "programming",
            "universiteto gyvenimas": "university life",
            "technologijų naujienos": "tech news",
            "duomenų bazės": "databases",
            "karjera IT srityje": "career in tech",
        }.get(topic, topic)
        hook_text = f"Did you know {topic} works differently than it looks?"
    else:
        hook_text = hook_template.format(topic=topic)

    data = {
        "primary_topic": topic,
        "secondary_topics": [_pick(seed, _LT_TOPICS, salt=3)],
        "content_format": content_format,
        "presentation_style": ["talking_head", "onscreen_captions"],
        "hook": {
            "text": hook_text,
            "type": hook_type,
            "mechanism": "creates_curiosity_gap",
        },
        "tone": ["informative", "conversational"],
        "story_structure": ["hook", "context", "main_point", "conclusion"],
        "audience_promise": "Explain the idea clearly in under a minute."
        if english
        else "Aiškiai paaiškinti mintį per minutę.",
        "emotional_angle": "curiosity",
        "cta_pattern": "follow_for_more",
        "editing_intensity": _pick(seed, ["low", "medium", "high"], salt=4),
        "estimated_pacing": _pick(seed, ["slow", "medium", "fast"], salt=5),
        "personal_story_level": round((seed % 100) / 100, 2),
        "educational_level": round(((seed // 7) % 100) / 100, 2),
        "visual_analysis_available": False,
        "transcript_available": False,
        "confidence": 0.55,
    }
    return json.dumps(data)


_BUILDERS = {
    "ContentAnalysisSchema": _build_content_analysis,
}
