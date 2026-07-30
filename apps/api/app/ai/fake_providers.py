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
from app.db.seed_data import CONTENT_FORMATS

_LT_TOPICS = [
    "dirbtinis intelektas",
    "programavimas",
    "universiteto gyvenimas",
    "technologijų naujienos",
    "duomenų bazės",
    "karjera IT srityje",
]
_TOPIC_EN = {
    "dirbtinis intelektas": "artificial intelligence",
    "programavimas": "programming",
    "universiteto gyvenimas": "university life",
    "technologijų naujienos": "tech news",
    "duomenų bazės": "databases",
    "karjera IT srityje": "career in tech",
}
_LT_HOOKS = [
    ("Ar žinojai, kad {topic} veikia visai kitaip, nei atrodo?", "provocative_question"),
    ("Prieš savaitę man nutiko kažkas, kas pakeitė požiūrį į {topic}.", "personal_anecdote"),
    ("Trys dalykai apie {topic}, kuriuos supratau per vėlai.", "listicle_promise"),
    ("Visi klysta dėl {topic} -- štai kodėl.", "myth_bust"),
]
_EN_HOOKS = [
    ("Did you know {topic} works differently than it looks?", "provocative_question"),
    ("Something happened last week that changed how I think about {topic}.", "personal_anecdote"),
    ("Three things about {topic} I learned way too late.", "listicle_promise"),
    ("Everyone gets {topic} wrong -- here's why.", "myth_bust"),
]
_FORMATS = [
    "edited_tech_explainer",
    "casual_talking_head",
    "grwm_story",
    "tech_news_recap",
    "screen_recording_demo",
    "myth_vs_fact",
]
_FORMAT_LABELS_LT = {fmt["code"]: fmt["label_lt"] for fmt in CONTENT_FORMATS}


def _topic_text(topic: str, english: bool) -> str:
    return _TOPIC_EN.get(topic, topic) if english else topic


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

    topic = _topic_text(topic, english)
    if english:
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


def _build_content_idea(prompt: str) -> str:
    import json

    seed = _seed(prompt)
    english = _is_english(prompt)
    topic = _topic_text(_pick(seed, _LT_TOPICS, salt=10), english)
    content_format = _pick(seed, _FORMATS, salt=11)
    hook_pool = _EN_HOOKS if english else _LT_HOOKS
    hooks = [hook_pool[(seed + i) % len(hook_pool)][0].format(topic=topic) for i in range(3)]
    format_label_lt = _FORMAT_LABELS_LT.get(content_format, content_format)

    if english:
        data = {
            "title": f"What nobody tells you about {topic}",
            "concept": f"A short video exploring an underrated angle on {topic}.",
            "content_pillar": topic,
            "recommended_format": content_format,
            "format_label_lt": format_label_lt,
            "why_it_fits_me": f"Builds on the creator's recurring interest in {topic}.",
            "inspiration_pattern": "Adapts a curiosity-gap hook structure seen in similar content.",
            "originality_note": "Uses the creator's own examples and phrasing, not the source's.",
            "hook_options": hooks,
            "outline": ["Hook", "Context", "Main point", "Takeaway"],
            "suggested_duration_seconds": 45 + (seed % 60),
            "production_effort": _pick(seed, ["low", "medium", "high"], salt=12),
        }
    else:
        data = {
            "title": f"Ką nedaug kas žino apie {topic}",
            "concept": f"Trumpas vaizdo įrašas apie neįprastą {topic} kampą.",
            "content_pillar": topic,
            "recommended_format": content_format,
            "format_label_lt": format_label_lt,
            "why_it_fits_me": f"Tęsia kūrėjo pasikartojantį susidomėjimą tema -- {topic}.",
            "inspiration_pattern": (
                "Perima smalsumo kabliuko struktūrą, matytą panašiame turinyje."
            ),
            "originality_note": (
                "Naudoja kūrėjo pačios pavyzdžius ir frazes, ne originalaus šaltinio."
            ),
            "hook_options": hooks,
            "outline": ["Kabliukas", "Kontekstas", "Pagrindinė mintis", "Išvada"],
            "suggested_duration_seconds": 45 + (seed % 60),
            "production_effort": _pick(seed, ["low", "medium", "high"], salt=12),
        }
    return json.dumps(data)


def _build_generated_brief(prompt: str) -> str:
    import json

    seed = _seed(prompt)
    english = _is_english(prompt)
    topic = _topic_text(_pick(seed, _LT_TOPICS, salt=20), english)
    recommended_format = _pick(seed, _FORMATS, salt=21)

    if english:
        data = {
            "objective": f"Clearly explain {topic} in under a minute.",
            "target_viewer": "Someone curious about technology but without deep background.",
            "promise": f"You'll understand {topic} well enough to explain it yourself.",
            "recommended_format": recommended_format,
            "recommended_duration_seconds": 45 + (seed % 30),
            "hook_choices": [
                f"Did you know {topic} works differently than it looks?",
                f"Here's what nobody tells you about {topic}.",
            ],
            "beats": [
                {"label": "Hook", "description": f"Open with a surprising claim about {topic}."},
                {"label": "Context", "description": "Give just enough background to follow."},
                {"label": "Main point", "description": f"Explain the core idea behind {topic}."},
                {"label": "Close", "description": "One-line takeaway plus a call to action."},
            ],
            "b_roll_suggestions": ["Screen recording of the concept", "Close-up reaction shot"],
            "on_screen_text": [topic.title(), "Follow for more"],
            "editing_notes": ["Cut on the hook's punchline", "Add captions throughout"],
            "closing_line": f"That's the real story behind {topic}.",
            "call_to_action": "Follow for more explainers like this.",
            "caption_options": [f"The truth about {topic}", f"{topic}, explained simply"],
            "hashtags": ["#tech", "#explainer"],
            "claims_to_verify": [
                f"Confirm the specific claim made about {topic} before publishing."
            ],
        }
    else:
        data = {
            "objective": f"Aiškiai paaiškinti {topic} per minutę.",
            "target_viewer": "Žmogus, besidomintis technologijomis, bet be gilių žinių.",
            "promise": f"Suprasi {topic} tiek, kad galėtum pats paaiškinti kitiems.",
            "recommended_format": recommended_format,
            "recommended_duration_seconds": 45 + (seed % 30),
            "hook_choices": [
                f"Ar žinojai, kad {topic} veikia visai kitaip, nei atrodo?",
                f"Štai ko niekas nesako apie {topic}.",
            ],
            "beats": [
                {"label": "Kabliukas", "description": f"Pradėk netikėtu teiginiu apie {topic}."},
                {
                    "label": "Kontekstas",
                    "description": "Duok tiek konteksto, kiek reikia sekti mintį.",
                },
                {"label": "Pagrindinė mintis", "description": f"Paaiškink esmę apie {topic}."},
                {"label": "Pabaiga", "description": "Viena išvados eilutė ir kvietimas veikti."},
            ],
            "b_roll_suggestions": ["Ekrano įrašas su koncepcija", "Artimas reakcijos kadras"],
            "on_screen_text": [topic.title(), "Sek daugiau"],
            "editing_notes": [
                "Kirpk ties kabliuko kulminacija",
                "Prirašyk subtitrus visame vaizdo įraše",
            ],
            "closing_line": f"Štai tikroji istorija apie {topic}.",
            "call_to_action": "Sek, kad nepraleistum daugiau tokių paaiškinimų.",
            "caption_options": [f"Tiesa apie {topic}", f"{topic}, paaiškinta paprastai"],
            "hashtags": ["#technologijos", "#paaiškinimas"],
            "claims_to_verify": [f"Patikrink konkretų teiginį apie {topic} prieš publikuojant."],
        }
    return json.dumps(data)


def _build_generated_script(prompt: str) -> str:
    import json

    seed = _seed(prompt)
    english = _is_english(prompt)
    topic = _topic_text(_pick(seed, _LT_TOPICS, salt=30), english)

    if english:
        data = {
            "spoken_lines": [
                f"Did you know {topic} works differently than it looks?",
                f"Here's the short version of {topic}.",
                "That's the part most people miss.",
                "Follow for more like this.",
            ],
            "editing_notes": ["Cut to a close-up on the hook", "Add captions throughout"],
            "estimated_duration_seconds": 40 + (seed % 30),
            "placeholders": [],
        }
    else:
        data = {
            "spoken_lines": [
                f"Ar žinojai, kad {topic} veikia visai kitaip, nei atrodo?",
                f"Štai trumpa {topic} versija.",
                "Tai dalis, kurią dauguma praleidžia.",
                "Sek, jei nori daugiau tokio turinio.",
            ],
            "editing_notes": [
                "Perjunk į artimą kadrą ties kabliuku",
                "Prirašyk subtitrus visame vaizdo įraše",
            ],
            "estimated_duration_seconds": 40 + (seed % 30),
            "placeholders": [],
        }
    return json.dumps(data)


def _build_media_placement_plan(prompt: str) -> str:
    import json

    seed = _seed(prompt)
    english = _is_english(prompt)
    topic = _topic_text(_pick(seed, _LT_TOPICS, salt=40), english)

    beats_match = re.search(r"Beats:\n(.*?)\n\n", prompt, re.DOTALL)
    beat_labels = [line.split(":", 1)[0] for line in beats_match.group(1).splitlines()] if (
        beats_match
    ) else ["Hook", "Context", "Main point", "Close"]

    image_count_match = re.search(r"Propose exactly (\d+) image placements", prompt)
    image_count = int(image_count_match.group(1)) if image_count_match else 5
    meme_count_match = re.search(r"Propose exactly (\d+) meme placements", prompt)
    meme_count = int(meme_count_match.group(1)) if meme_count_match else 5

    if english:
        caption_pairs = [
            ["When you finally understand {topic}", "vs. explaining it to someone else"],
            ["Me pretending {topic} is simple", "{topic}, actually"],
            ["Nobody:", "Me, thinking about {topic} at 2am"],
        ]
    else:
        caption_pairs = [
            ["Kai pagaliau supranti {topic}", "prieš tai, kai bandai tai paaiškinti kitam"],
            ["Aš, sakydamas, kad {topic} yra paprasta", "{topic}, iš tikrųjų"],
            ["Niekas:", "Aš, 2 val. nakties mąstantis apie {topic}"],
        ]

    def _placement_for(i: int) -> str:
        label = beat_labels[i % len(beat_labels)]
        return (
            f"During the '{label}' beat"
            if english
            else f"Ties '{label}' etapo"
        )

    data = {
        "image_placements": [
            {
                "placement": _placement_for(i),
                "search_query": f"{topic} concept" if english else topic,
            }
            for i in range(image_count)
        ],
        "meme_placements": [
            {
                "placement": _placement_for(i),
                "caption_lines": [
                    line.format(topic=topic) for line in caption_pairs[i % len(caption_pairs)]
                ],
            }
            for i in range(meme_count)
        ],
    }
    return json.dumps(data)


_BUILDERS = {
    "ContentAnalysisSchema": _build_content_analysis,
    "ContentIdeaSchema": _build_content_idea,
    "GeneratedBriefSchema": _build_generated_brief,
    "GeneratedScriptSchema": _build_generated_script,
    "MediaPlacementPlanSchema": _build_media_placement_plan,
}
