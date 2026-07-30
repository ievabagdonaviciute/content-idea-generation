from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_format import ContentFormat
from app.models.idea import ContentIdea, GeneratedBrief
from app.services.idea_media import BriefRequiredError, generate_idea_media


async def _seed_idea(session: AsyncSession, *, with_brief: bool) -> ContentIdea:
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

    if with_brief:
        brief = GeneratedBrief(
            objective="Aiškiai paaiškinti superintelektą per minutę.",
            target_viewer="Žmogus, besidomintis AI.",
            promise="Suprasi, kas yra superintelektas.",
            recommended_format="edited_tech_explainer",
            recommended_duration_seconds=60,
            hook_choices=["Ar žinojai, kad AI veikia visai kitaip?"],
            beats=[
                {"label": "Kabliukas", "description": "Pradėk klausimu apie superintelektą."},
                {"label": "Pagrindinė mintis", "description": "Paaiškink superintelektą."},
            ],
            closing_line="Štai kodėl superintelektas svarbus.",
            call_to_action="Sek daugiau.",
            output_language="lt",
        )
        brief.idea = idea
        session.add(brief)
        await session.flush()

    # Forces an explicit, async-safe load of the relationship (whether or not a
    # brief was just created) instead of leaving it to a first-access lazy-load,
    # which raises MissingGreenlet under the async ORM -- see the identical
    # pattern in app/pipelines/analysis_pipeline.py. The real caller
    # (IdeaRepository.get_by_id) always eager-loads this the same way.
    await session.refresh(idea, attribute_names=["brief"])
    return idea


async def test_generate_idea_media_requires_a_brief(db_session: AsyncSession) -> None:
    idea = await _seed_idea(db_session, with_brief=False)

    with pytest.raises(BriefRequiredError):
        await generate_idea_media(db_session, idea)


async def test_generate_idea_media_creates_placed_images_and_memes(
    db_session: AsyncSession,
) -> None:
    idea = await _seed_idea(db_session, with_brief=True)

    media = await generate_idea_media(db_session, idea)

    assert media.idea_id == idea.id
    assert len(media.images) == 5
    assert all(img["url"] and img["placement"] for img in media.images)
    assert len(media.memes) == 5
    assert all(meme["caption_lines"] and meme["placement"] for meme in media.memes)


async def test_regenerating_media_updates_existing_record_in_place(
    db_session: AsyncSession,
) -> None:
    idea = await _seed_idea(db_session, with_brief=True)

    first = await generate_idea_media(db_session, idea)
    second = await generate_idea_media(db_session, idea)

    assert first.id == second.id
