"""Generates a spoken script for one ContentIdea in a given mode. Same
generate-and-validate pattern as idea/brief generation -- see
docs/AI_PIPELINE.md "Briefs and scripts". Callers must load ``idea`` with its
``brief``/``script`` relationships eagerly (see
app/repositories/idea_repository.py) since this runs in an async session.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_text_provider
from app.ai.json_generation import generate_validated_json
from app.ai.prompts.script_modes import SCRIPT_MODES
from app.ai.prompts.script_prompts import ScriptPromptContext, build_script_prompt
from app.models.idea import ContentIdea, GeneratedScript
from app.schemas.script import GeneratedScriptSchema


class InvalidScriptModeError(ValueError):
    pass


async def generate_script(session: AsyncSession, idea: ContentIdea, mode: str) -> GeneratedScript:
    if mode not in SCRIPT_MODES:
        raise InvalidScriptModeError(f"Unknown script mode: {mode!r}. Allowed: {SCRIPT_MODES}")

    brief_beats = (
        [f"{beat['label']}: {beat['description']}" for beat in idea.brief.beats]
        if idea.brief is not None
        else []
    )
    prompt = build_script_prompt(
        ScriptPromptContext(
            idea_title=idea.title,
            idea_concept=idea.concept,
            mode=mode,
            hook_options=idea.hook_options,
            brief_beats=brief_beats,
            output_language=idea.output_language,
        )
    )
    data = await generate_validated_json(get_text_provider(), prompt, GeneratedScriptSchema)

    if idea.script is not None:
        script = idea.script
    else:
        # Assigning through the relationship (not just the idea_id FK) keeps
        # idea.script in sync in memory via back_populates -- see the identical
        # fix in app/pipelines/analysis_pipeline.py::_upsert_content_analysis.
        script = GeneratedScript()
        script.idea = idea
    script.mode = mode
    script.spoken_lines = data.spoken_lines
    script.editing_notes = data.editing_notes
    script.estimated_duration_seconds = data.estimated_duration_seconds
    script.placeholders = data.placeholders
    script.output_language = idea.output_language

    session.add(script)
    await session.flush()
    return script
