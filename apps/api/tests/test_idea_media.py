from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_format import ContentFormat
from app.models.idea import ContentIdea
from app.services.idea_media import generate_idea_media


async def _seed_idea(session: AsyncSession) -> ContentIdea:
    session.add(
        ContentFormat(code="edited_tech_explainer", label_en="Explainer", label_lt="Paaiškinimas")
    )
    await session.flush()
    idea = ContentIdea(
        title="Ką nedaug kas žino apie AI",
        concept="Trumpas vaizdo įrašas apie neįprastą AI kampą.",
        content_pillar="dirbtinis intelektas",
        recommended_format="edited_tech_explainer",
        format_label_lt="Paaiškinimas",
        why_it_fits_me="Tęsia kūrėjo susidomėjimą AI tema.",
        novelty_level="aligned",
        hook_options=["Ar žinojai, kad AI veikia visai kitaip?"],
        output_language="lt",
    )
    session.add(idea)
    await session.flush()
    return idea


async def test_generate_idea_media_creates_images_and_memes(db_session: AsyncSession) -> None:
    idea = await _seed_idea(db_session)

    media = await generate_idea_media(db_session, idea)

    assert media.idea_id == idea.id
    assert len(media.images) == 5
    assert all(img["url"] for img in media.images)
    assert len(media.memes) == 5
    assert all(meme["caption_lines"] for meme in media.memes)


async def test_regenerating_media_updates_existing_record_in_place(
    db_session: AsyncSession,
) -> None:
    idea = await _seed_idea(db_session)

    first = await generate_idea_media(db_session, idea)
    second = await generate_idea_media(db_session, idea)

    assert first.id == second.id
