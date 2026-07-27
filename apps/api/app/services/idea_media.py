"""Sources images and captioned memes for one ContentIdea, so a creator can pull
production-ready visuals for editing without leaving Kadro. See
docs/MEDIA_SOURCING.md.

Images come straight from the image search provider (Pexels, or a fake). Memes
combine the meme provider's most-popular templates with AI-written captions
relevant to the idea -- the caption generation follows the same
generate-and-validate pattern as idea/brief/script generation
(app/ai/json_generation.py).
"""

from __future__ import annotations

from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_text_provider
from app.ai.json_generation import generate_validated_json
from app.ai.prompts.meme_prompts import MemeCaptionPromptContext, build_meme_caption_prompt
from app.integrations.media.factory import get_image_provider, get_meme_provider
from app.models.idea import ContentIdea, IdeaSourcedMedia
from app.schemas.meme import MemeCaptionsSchema

IMAGE_COUNT = 5
MEME_COUNT = 5


async def generate_idea_media(session: AsyncSession, idea: ContentIdea) -> IdeaSourcedMedia:
    query = f"{idea.content_pillar} {idea.title}"
    images = await get_image_provider().search(query, IMAGE_COUNT)

    meme_provider = get_meme_provider()
    templates = await meme_provider.list_templates(MEME_COUNT)

    prompt = build_meme_caption_prompt(
        MemeCaptionPromptContext(
            idea_title=idea.title,
            idea_concept=idea.concept,
            hook_options=idea.hook_options,
            count=len(templates),
            output_language=idea.output_language,
        )
    )
    caption_data = await generate_validated_json(get_text_provider(), prompt, MemeCaptionsSchema)

    memes = [
        await meme_provider.caption(template, caption.lines)
        for template, caption in zip(templates, caption_data.captions, strict=False)
    ]

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

    record.images = [asdict(img) for img in images]
    record.memes = [asdict(meme) for meme in memes]

    session.add(record)
    await session.flush()
    return record
