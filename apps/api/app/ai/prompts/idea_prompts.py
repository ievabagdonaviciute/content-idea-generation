"""Idea-generation prompt builder. See docs/AI_PIPELINE.md "Idea generation" and
docs/PRODUCT_SPEC.md "Inspiration vs. imitation": ideas may borrow structural
patterns (hook mechanism, narrative structure, pacing) but must never reproduce
another creator's exact hook text, jokes, or examples.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.ai.prompts.voice import voice_guide
from app.db.seed_data import CONTENT_FORMATS

_NOVELTY_GUIDANCE = {
    "aligned": (
        "Stay close to the creator's established pillars and formats -- a safe, "
        "on-brand idea."
    ),
    "stretch": (
        "Stretch one dimension (format, angle, or tone) away from the established "
        "pattern while keeping the topic recognizably theirs."
    ),
    "experimental": (
        "Explore a genuinely new angle, format, or topic adjacent to the creator's "
        "identity -- more novel, still plausible for this creator."
    ),
}


@dataclass
class IdeaPromptContext:
    novelty_level: str  # "aligned" | "stretch" | "experimental"
    profile_summary: str
    similar_posts_summary: str
    inspiration_summary: str
    feedback_summary: str
    instructions: str | None = None
    excluded_subjects: list[str] = field(default_factory=list)
    output_language: str = "lt"


def _format_list() -> str:
    return ", ".join(f"{fmt['code']}" for fmt in CONTENT_FORMATS)


def build_idea_prompt(context: IdeaPromptContext) -> str:
    parts = [
        "You are generating one original short-form video idea for a personal "
        "TikTok content planning tool, for the creator described by the profile "
        "below. Do not invent facts about the creator that aren't supported by "
        "the given material.",
        f"output_language: {context.output_language}",
        f"novelty_level: {context.novelty_level} -- {_NOVELTY_GUIDANCE[context.novelty_level]}",
        f"Allowed recommended_format codes: {_format_list()}",
        voice_guide(context.output_language),
        f"Creator content profile: {context.profile_summary}",
        f"Most similar existing posts (avoid duplicating these): {context.similar_posts_summary}",
        f"Recent inspiration saved by the creator: {context.inspiration_summary or '(none)'}",
        f"Recent feedback on past ideas: {context.feedback_summary or '(none)'}",
        f"User instructions: {context.instructions or '(none)'}",
        f"Subjects to avoid: {', '.join(context.excluded_subjects) or '(none)'}",
        "Never reproduce another creator's exact hook text, jokes, or examples -- "
        "you may borrow a structural pattern (hook mechanism, narrative structure, "
        "pacing) but must state how this idea differs from its source in "
        "originality_note.",
        "Respond with a single JSON object matching the required schema exactly.",
    ]
    return "\n\n".join(parts)
