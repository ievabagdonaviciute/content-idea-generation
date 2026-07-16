from __future__ import annotations

from dataclasses import dataclass

from app.ai.prompts.voice import voice_guide
from app.db.seed_data import CONTENT_FORMATS


@dataclass
class AnalysisPromptContext:
    caption: str | None
    creator_notes: str | None
    transcript: str | None
    visual_description: str | None
    output_language: str = "lt"


def _format_list() -> str:
    return ", ".join(f"{fmt['code']}" for fmt in CONTENT_FORMATS)


def build_content_analysis_prompt(context: AnalysisPromptContext) -> str:
    parts = [
        "You are analyzing one short-form video for a personal TikTok content "
        "planning tool. Extract structured features -- do not invent facts that "
        "aren't supported by the given material.",
        f"output_language: {context.output_language}",
        f"Allowed content_format codes: {_format_list()}",
        voice_guide(context.output_language),
        f"Caption: {context.caption or '(none)'}",
        f"Creator notes: {context.creator_notes or '(none)'}",
        f"Transcript: {context.transcript or '(not available)'}",
        f"Visual description: {context.visual_description or '(not available)'}",
        "If the transcript is not available, set transcript_available to false and "
        "do not guess at spoken content. If no visual description is available, set "
        "visual_analysis_available to false and do not invent visual details.",
        "Respond with a single JSON object matching the required schema exactly.",
    ]
    return "\n\n".join(parts)
