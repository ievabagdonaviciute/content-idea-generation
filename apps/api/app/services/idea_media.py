"""Sources images and captioned memes for one ContentIdea, each tied to a
specific placement in the idea's finalized brief -- so a creator can pull
production-ready visuals for editing and know exactly where each one goes. See
docs/MEDIA_SOURCING.md.

Requires a brief: without one there is nothing to place images against, so
sourcing media before a brief exists is a user error (BriefRequiredError), not
an AI/provider failure. The AI text provider first plans placements (one search
query or caption per placement, each pointing at a specific beat/moment in the
brief -- app/ai/prompts/media_placement_prompts.py), then each placement is
resolved to a real image (Pexels, or a fake) or a real captioned meme (Imgflip,
or a fake).
"""

from __future__ import annotations

from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_text_provider
from app.ai.json_generation import generate_validated_json
from app.ai.prompts.media_placement_prompts import (
    MediaPlacementPromptContext,
    build_media_placement_prompt,
)
from app.integrations.media.factory import get_image_provider, get_meme_provider
from app.models.idea import ContentIdea, IdeaSourcedMedia
from app.schemas.media_placement import MediaPlacementPlanSchema

IMAGE_COUNT = 5
MEME_COUNT = 5


class BriefRequiredError(RuntimeError):
    pass


async def generate_idea_media(session: AsyncSession, idea: ContentIdea) -> IdeaSourcedMedia:
    brief = idea.brief
    if brief is None:
        raise BriefRequiredError(
            "Generate a brief for this idea before sourcing images/memes -- "
            "each one is placed against a specific beat in the brief."
        )

    prompt = build_media_placement_prompt(
        MediaPlacementPromptContext(
            idea_title=idea.title,
            idea_concept=idea.concept,
            brief_objective=brief.objective,
            brief_promise=brief.promise,
            beats=[f"{beat['label']}: {beat['description']}" for beat in brief.beats],
            hook_choices=brief.hook_choices,
            on_screen_text=brief.on_screen_text,
            closing_line=brief.closing_line,
            call_to_action=brief.call_to_action,
            image_count=IMAGE_COUNT,
            meme_count=MEME_COUNT,
            output_language=idea.output_language,
        )
    )
    plan = await generate_validated_json(get_text_provider(), prompt, MediaPlacementPlanSchema)

    image_provider = get_image_provider()
    images: list[dict] = []
    for image_placement in plan.image_placements:
        results = await image_provider.search(image_placement.search_query, 1)
        if not results:
            continue
        image_dict = asdict(results[0])
        image_dict["placement"] = image_placement.placement
        images.append(image_dict)

    meme_provider = get_meme_provider()
    templates = await meme_provider.list_templates(len(plan.meme_placements))
    memes: list[dict] = []
    for template, meme_placement in zip(templates, plan.meme_placements, strict=False):
        meme = await meme_provider.caption(template, meme_placement.caption_lines)
        meme_dict = asdict(meme)
        meme_dict["placement"] = meme_placement.placement
        memes.append(meme_dict)

    # Queried directly by idea_id rather than via ``idea.sourced_media`` -- that
    # relationship attribute may not be loaded on ``idea`` (lazy-loading it from
    # plain sync attribute access raises ``MissingGreenlet`` under the async ORM,
    # the same failure mode fixed in app/pipelines/analysis_pipeline.py), and this
    # way behaves identically regardless of how the caller fetched ``idea``.
    existing = (
        await session.execute(
            select(IdeaSourcedMedia).where(IdeaSourcedMedia.idea_id == idea.id)
        )
    ).scalar_one_or_none()
    if existing is not None:
        record = existing
    else:
        record = IdeaSourcedMedia()
        record.idea = idea

    record.images = images
    record.memes = memes

    session.add(record)
    await session.flush()
    return record
