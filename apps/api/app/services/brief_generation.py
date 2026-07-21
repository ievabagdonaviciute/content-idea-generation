"""Generates a production brief for one ContentIdea. Same generate-and-validate
pattern as idea generation -- see docs/AI_PIPELINE.md "Briefs and scripts".
Callers must load ``idea`` with its ``brief`` relationship eagerly (see
app/repositories/idea_repository.py) since this runs in an async session.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_text_provider
from app.ai.json_generation import generate_validated_json
from app.ai.prompts.brief_prompts import BriefPromptContext, build_brief_prompt
from app.models.idea import ContentIdea, GeneratedBrief
from app.schemas.brief import GeneratedBriefSchema


async def generate_brief(session: AsyncSession, idea: ContentIdea) -> GeneratedBrief:
    prompt = build_brief_prompt(
        BriefPromptContext(
            idea_title=idea.title,
            idea_concept=idea.concept,
            recommended_format=idea.recommended_format,
            hook_options=idea.hook_options,
            outline=idea.outline,
            suggested_duration_seconds=idea.suggested_duration_seconds,
            output_language=idea.output_language,
        )
    )
    data = await generate_validated_json(get_text_provider(), prompt, GeneratedBriefSchema)

    if idea.brief is not None:
        brief = idea.brief
    else:
        # Assigning through the relationship (not just the idea_id FK) keeps
        # idea.brief in sync in memory via back_populates -- see the identical
        # fix in app/pipelines/analysis_pipeline.py::_upsert_content_analysis.
        brief = GeneratedBrief()
        brief.idea = idea
    brief.objective = data.objective
    brief.target_viewer = data.target_viewer
    brief.promise = data.promise
    brief.recommended_format = data.recommended_format
    brief.recommended_duration_seconds = data.recommended_duration_seconds
    brief.hook_choices = data.hook_choices
    brief.beats = [beat.model_dump() for beat in data.beats]
    brief.b_roll_suggestions = data.b_roll_suggestions
    brief.on_screen_text = data.on_screen_text
    brief.editing_notes = data.editing_notes
    brief.closing_line = data.closing_line
    brief.call_to_action = data.call_to_action
    brief.caption_options = data.caption_options
    brief.hashtags = data.hashtags
    brief.claims_to_verify = data.claims_to_verify
    brief.output_language = idea.output_language

    session.add(brief)
    await session.flush()
    return brief
