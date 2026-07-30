"""Media-placement prompt builder. See docs/MEDIA_SOURCING.md. Plans images and
memes against a *finalized brief* (not the raw idea) so each item can be tied to
a specific beat/moment rather than being generically "about the topic" -- e.g. a
brief beat that says "superintelligence" should surface a placement suggestion
for that exact moment, not a vague AI-themed photo.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MediaPlacementPromptContext:
    idea_title: str
    idea_concept: str
    brief_objective: str
    brief_promise: str
    beats: list[str]
    hook_choices: list[str]
    on_screen_text: list[str]
    closing_line: str
    call_to_action: str
    image_count: int
    meme_count: int
    output_language: str = "lt"


def build_media_placement_prompt(context: MediaPlacementPromptContext) -> str:
    parts = [
        "You are planning b-roll images and memes for a short-form video, based "
        "on its finalized production brief below. For every item, name the "
        "specific moment in the brief where it belongs (quote or reference the "
        "exact beat label/description, hook, on-screen text, or closing line) "
        "and tie the image/meme concretely to what is actually said or shown at "
        "that moment -- e.g. if a beat mentions \"superintelligence\", a fitting "
        "meme is a giant-brained figure, not a generic technology photo. Never "
        "propose an item with no specific placement.",
        f"output_language: {context.output_language}",
        f"Idea: {context.idea_title} -- {context.idea_concept}",
        f"Brief objective: {context.brief_objective}",
        f"Brief promise: {context.brief_promise}",
        "Beats:\n" + "\n".join(context.beats),
        f"Hook choices: {', '.join(context.hook_choices)}",
        f"On-screen text: {', '.join(context.on_screen_text) or '(none)'}",
        f"Closing line: {context.closing_line}",
        f"Call to action: {context.call_to_action}",
        f"Propose exactly {context.image_count} image placements. Each needs a "
        "short, concrete, visual stock-photo search query (English works best "
        "for photo search regardless of output_language) and a placement "
        "description naming the specific beat/moment.",
        f"Propose exactly {context.meme_count} meme placements. Each needs 1-2 "
        "short caption lines (in output_language) and a placement description "
        "naming the specific beat/moment.",
        "Respond with a single JSON object matching the required schema exactly.",
    ]
    return "\n\n".join(parts)
