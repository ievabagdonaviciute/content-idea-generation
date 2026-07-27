"""Meme-caption prompt builder. See docs/MEDIA_SOURCING.md. Captions are
generic setup/punchline pairs relatable to the idea's topic -- not tied to one
specific meme template's visual structure, since templates are chosen
separately from Imgflip's most-popular list.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MemeCaptionPromptContext:
    idea_title: str
    idea_concept: str
    hook_options: list[str]
    count: int
    output_language: str = "lt"


def build_meme_caption_prompt(context: MemeCaptionPromptContext) -> str:
    parts = [
        "You are writing short, funny meme captions for a short-form video "
        "creator to use while editing a video about the idea below. Each "
        "caption is a generic setup/punchline pair (1-2 short lines) that would "
        "make sense overlaid on a popular meme template -- do not reference a "
        "specific template's visual layout, just write relatable, punchy lines "
        "about the topic.",
        f"output_language: {context.output_language}",
        f"Idea title: {context.idea_title}",
        f"Idea concept: {context.idea_concept}",
        f"Hook options: {', '.join(context.hook_options)}",
        f"Generate exactly {context.count} distinct caption sets.",
        "Respond with a single JSON object matching the required schema exactly.",
    ]
    return "\n\n".join(parts)
