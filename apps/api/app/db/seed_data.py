"""Reference/seed data shared by the seed CLI command and tests.

``CONTENT_FORMATS`` is the canonical, extendable list of recognized content formats
(docs/PRODUCT_SPEC.md). Adding a new format means adding a row here, not touching an
enum used throughout the codebase.
"""

from __future__ import annotations

CONTENT_FORMATS: list[dict[str, str]] = [
    {
        "code": "edited_tech_explainer",
        "label_en": "Professionally edited technology explainer",
        "label_lt": "Profesionaliai sumontuotas technologijų paaiškinimas",
        "description": "Scripted, tightly edited explainer with captions and cutaways.",
    },
    {
        "code": "casual_talking_head",
        "label_en": "Casual talking-to-camera video",
        "label_lt": "Laisvas pasakojimas į kamerą",
        "description": "Unscripted or lightly scripted, single continuous take.",
    },
    {
        "code": "grwm_story",
        "label_en": "Get-ready-with-me story",
        "label_lt": "Get ready with me su asmenine istorija",
        "description": "Routine footage interleaved with a personal narrative.",
    },
    {
        "code": "personal_experience_opinion",
        "label_en": "Personal experience or opinion",
        "label_lt": "Asmeninė patirtis ar nuomonė",
        "description": "First-person recount of an experience or a stated opinion.",
    },
    {
        "code": "tech_news_recap",
        "label_en": "Technology news recap",
        "label_lt": "Technologijų naujienų apžvalga",
        "description": "Summary of a recent tech event or announcement plus a take.",
    },
    {
        "code": "educational_history_explainer",
        "label_en": "Educational historical explanation",
        "label_lt": "Istorinis edukacinis paaiškinimas",
        "description": "Explains the history behind a technology or idea.",
    },
    {
        "code": "comment_response",
        "label_en": "Response to a comment",
        "label_lt": "Atsakymas į komentarą",
        "description": "Directly addresses a viewer comment or question.",
    },
    {
        "code": "vlog",
        "label_en": "Vlog",
        "label_lt": "Vlogas",
        "description": "Day-in-the-life or diary-style footage.",
    },
    {
        "code": "voiceover_broll",
        "label_en": "Voice-over with B-roll",
        "label_lt": "Balso perdavimas su B-roll vaizdais",
        "description": "Narration over supporting footage, no on-camera talking head.",
    },
    {
        "code": "screen_recording_demo",
        "label_en": "Screen recording or demonstration",
        "label_lt": "Ekrano įrašas ar demonstracija",
        "description": "Screen capture walking through a tool, app, or workflow.",
    },
    {
        "code": "list_ranking",
        "label_en": "List or ranking",
        "label_lt": "Sąrašas ar reitingas",
        "description": "Enumerated items, ranked or unranked.",
    },
    {
        "code": "reaction",
        "label_en": "Reaction",
        "label_lt": "Reakcijos vaizdo įrašas",
        "description": "Reacting to another piece of content on camera.",
    },
    {
        "code": "myth_vs_fact",
        "label_en": "Myth-versus-fact explanation",
        "label_lt": "Mitas prieš faktą",
        "description": "Contrasts a common misconception with the accurate fact.",
    },
    {
        "code": "university_engineering_story",
        "label_en": "University or engineering-life story",
        "label_lt": "Universiteto ar inžinerijos gyvenimo istorija",
        "description": "Personal story rooted in studies or engineering work.",
    },
    {
        "code": "interview_style_answer",
        "label_en": "Interview-style answer",
        "label_lt": "Atsakymas interviu stiliumi",
        "description": "Answers a posed question as if in an interview.",
    },
    {
        "code": "trend_adapted_educational",
        "label_en": "Trend adapted to an educational subject",
        "label_lt": "Trendas, pritaikytas edukacinei temai",
        "description": "A popular trend format repurposed to teach something.",
    },
]
