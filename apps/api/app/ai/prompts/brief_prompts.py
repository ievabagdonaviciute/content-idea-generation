"""Production-brief prompt builder. See docs/AI_PIPELINE.md "Briefs and
scripts"."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.ai.prompts.voice import voice_guide


@dataclass
class BriefPromptContext:
    idea_title: str
    idea_concept: str
    recommended_format: str
    hook_options: list[str]
    outline: list[str] = field(default_factory=list)
    suggested_duration_seconds: int = 60
    output_language: str = "lt"


def build_brief_prompt(context: BriefPromptContext) -> str:
    parts = [
        "You are turning one approved short-form video idea into a full "
        "production brief for a personal TikTok content planning tool.",
        f"output_language: {context.output_language}",
        voice_guide(context.output_language),
        f"Idea title: {context.idea_title}",
        f"Idea concept: {context.idea_concept}",
        f"Recommended format: {context.recommended_format}",
        f"Hook options already generated: {'; '.join(context.hook_options)}",
        f"Outline already generated: {'; '.join(context.outline) or '(none)'}",
        f"Suggested duration: {context.suggested_duration_seconds} seconds",
        "Produce a beat-by-beat production brief: objective, target viewer, "
        "promise, hook choices, beats, b-roll suggestions, on-screen text, "
        "editing notes, closing line, call to action, caption options, hashtags, "
        "and any claims that should be fact-checked before publishing.",
        "Respond with a single JSON object matching the required schema exactly.",
    ]
    return "\n\n".join(parts)
