"""Spoken-script prompt builder. See docs/AI_PIPELINE.md "Briefs and scripts"
and docs/LITHUANIAN_GENERATION_GUIDE.md for mode-specific structural guidance."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.ai.prompts.script_modes import script_mode_guidance
from app.ai.prompts.voice import voice_guide


@dataclass
class ScriptPromptContext:
    idea_title: str
    idea_concept: str
    mode: str
    hook_options: list[str]
    brief_beats: list[str] = field(default_factory=list)
    output_language: str = "lt"


def build_script_prompt(context: ScriptPromptContext) -> str:
    parts = [
        "You are writing a full spoken script for one short-form video, for a "
        "personal TikTok content planning tool.",
        f"output_language: {context.output_language}",
        f"mode: {context.mode}",
        script_mode_guidance(context.mode, context.output_language),
        voice_guide(context.output_language),
        f"Idea title: {context.idea_title}",
        f"Idea concept: {context.idea_concept}",
        f"Hook options: {'; '.join(context.hook_options)}",
        f"Brief beats: {'; '.join(context.brief_beats) if context.brief_beats else '(none)'}",
        "Never fabricate a personal experience/anecdote as if it happened -- use "
        "an explicit placeholder for any detail you cannot know. Never repeat the "
        "hook verbatim as the conclusion. Keep spoken text and editing directions "
        "strictly separate -- spoken_lines must contain only words to be said "
        "aloud, never a bracketed instruction.",
        "Respond with a single JSON object matching the required schema exactly.",
    ]
    return "\n\n".join(parts)
