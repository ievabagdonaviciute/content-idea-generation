from __future__ import annotations

import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.json_generation import JsonGenerationError
from app.api.deps import get_session
from app.integrations.media.imgflip import ImgflipError
from app.models.idea import FEEDBACK_RATINGS, IDEA_STATUSES
from app.repositories.idea_repository import IdeaRepository
from app.repositories.inspiration_repository import InspirationRepository
from app.schemas.common import Page
from app.schemas.ideas import (
    ContentIdeaOut,
    GeneratedBriefOut,
    GeneratedScriptOut,
    IdeaFeedbackRequest,
    IdeaGenerateRequest,
    IdeaSourcedMediaOut,
    IdeaStatusUpdateRequest,
    ScriptGenerateRequest,
)
from app.services.brief_generation import generate_brief
from app.services.idea_generation import IdeaGenerationRequest, generate_ideas
from app.services.idea_media import generate_idea_media
from app.services.inspiration_usage import set_inspiration_used
from app.services.script_generation import InvalidScriptModeError, generate_script

router = APIRouter(prefix="/ideas", tags=["ideas"])

# The AI/image/meme provider is an external HTTP dependency (timeouts, rate
# limits, or the repair-retry loop exhausting its attempts) -- generation
# endpoints must report that as a clean 502, never let it surface as an
# unhandled 500 traceback.
_AI_PROVIDER_ERRORS = (JsonGenerationError, httpx.HTTPError, ImgflipError)


@router.post("/generate", response_model=list[ContentIdeaOut])
async def generate_ideas_endpoint(
    body: IdeaGenerateRequest, session: AsyncSession = Depends(get_session)
) -> list[ContentIdeaOut]:
    try:
        ideas = await generate_ideas(
            session,
            IdeaGenerationRequest(
                count=body.count,
                content_pillar=body.content_pillar,
                recommended_format=body.recommended_format,
                instructions=body.instructions,
                excluded_subjects=body.excluded_subjects,
                output_language=body.output_language,
            ),
        )
    except _AI_PROVIDER_ERRORS as exc:
        raise HTTPException(status_code=502, detail=f"AI idea generation failed: {exc}") from exc
    await session.commit()
    return [ContentIdeaOut.model_validate(idea) for idea in ideas]


@router.get("", response_model=Page[ContentIdeaOut])
async def list_ideas(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> Page[ContentIdeaOut]:
    if status is not None and status not in IDEA_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {IDEA_STATUSES}")
    repo = IdeaRepository(session)
    ideas = await repo.list_all(limit=limit, offset=offset, status=status)
    return Page(
        items=[ContentIdeaOut.model_validate(idea) for idea in ideas],
        total=len(ideas),
        limit=limit,
        offset=offset,
    )


@router.get("/{idea_id}", response_model=ContentIdeaOut)
async def get_idea(
    idea_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> ContentIdeaOut:
    repo = IdeaRepository(session)
    idea = await repo.get_by_id(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    return ContentIdeaOut.model_validate(idea)


@router.post("/{idea_id}/feedback", response_model=ContentIdeaOut)
async def submit_feedback(
    idea_id: uuid.UUID, body: IdeaFeedbackRequest, session: AsyncSession = Depends(get_session)
) -> ContentIdeaOut:
    if body.rating not in FEEDBACK_RATINGS:
        raise HTTPException(status_code=422, detail=f"rating must be one of {FEEDBACK_RATINGS}")
    repo = IdeaRepository(session)
    idea = await repo.get_by_id(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    await repo.add_feedback(idea, body.rating, body.comment)
    await session.commit()
    return ContentIdeaOut.model_validate(idea)


@router.post("/{idea_id}/brief", response_model=GeneratedBriefOut)
async def generate_brief_endpoint(
    idea_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> GeneratedBriefOut:
    repo = IdeaRepository(session)
    idea = await repo.get_by_id(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    try:
        brief = await generate_brief(session, idea)
    except _AI_PROVIDER_ERRORS as exc:
        raise HTTPException(status_code=502, detail=f"AI brief generation failed: {exc}") from exc
    await session.commit()
    return GeneratedBriefOut.model_validate(brief)


@router.get("/{idea_id}/brief", response_model=GeneratedBriefOut)
async def get_brief_endpoint(
    idea_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> GeneratedBriefOut:
    repo = IdeaRepository(session)
    idea = await repo.get_by_id(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    if idea.brief is None:
        raise HTTPException(status_code=404, detail="No brief generated yet for this idea")
    return GeneratedBriefOut.model_validate(idea.brief)


@router.post("/{idea_id}/script", response_model=GeneratedScriptOut)
async def generate_script_endpoint(
    idea_id: uuid.UUID, body: ScriptGenerateRequest, session: AsyncSession = Depends(get_session)
) -> GeneratedScriptOut:
    repo = IdeaRepository(session)
    idea = await repo.get_by_id(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    try:
        script = await generate_script(session, idea, body.mode)
    except InvalidScriptModeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except _AI_PROVIDER_ERRORS as exc:
        raise HTTPException(status_code=502, detail=f"AI script generation failed: {exc}") from exc
    await session.commit()
    return GeneratedScriptOut.model_validate(script)


@router.get("/{idea_id}/script", response_model=GeneratedScriptOut)
async def get_script_endpoint(
    idea_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> GeneratedScriptOut:
    repo = IdeaRepository(session)
    idea = await repo.get_by_id(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    if idea.script is None:
        raise HTTPException(status_code=404, detail="No script generated yet for this idea")
    return GeneratedScriptOut.model_validate(idea.script)


@router.post("/{idea_id}/media", response_model=IdeaSourcedMediaOut)
async def generate_idea_media_endpoint(
    idea_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> IdeaSourcedMediaOut:
    repo = IdeaRepository(session)
    idea = await repo.get_by_id(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    try:
        media = await generate_idea_media(session, idea)
    except _AI_PROVIDER_ERRORS as exc:
        raise HTTPException(status_code=502, detail=f"Media sourcing failed: {exc}") from exc
    await session.commit()
    return IdeaSourcedMediaOut.model_validate(media)


@router.get("/{idea_id}/media", response_model=IdeaSourcedMediaOut)
async def get_idea_media_endpoint(
    idea_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> IdeaSourcedMediaOut:
    repo = IdeaRepository(session)
    idea = await repo.get_by_id(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    if idea.sourced_media is None:
        raise HTTPException(status_code=404, detail="No media sourced yet for this idea")
    return IdeaSourcedMediaOut.model_validate(idea.sourced_media)


@router.post("/{idea_id}/status", response_model=ContentIdeaOut)
async def update_idea_status(
    idea_id: uuid.UUID, body: IdeaStatusUpdateRequest, session: AsyncSession = Depends(get_session)
) -> ContentIdeaOut:
    if body.status not in IDEA_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {IDEA_STATUSES}")
    repo = IdeaRepository(session)
    idea = await repo.get_by_id(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    idea.status = body.status

    if body.status == "done":
        # Closes the loop with inspiration: finishing a video means the TikTok(s)
        # it was based on won't be suggested as idea-generation context again --
        # see docs/DATA_MODEL.md and app/services/inspiration_usage.py.
        inspiration_repo = InspirationRepository(session)
        seen_inspiration_ids = {
            s.inspiration_item_id for s in idea.sources if s.inspiration_item_id
        }
        for inspiration_item_id in seen_inspiration_ids:
            item = await inspiration_repo.get_by_id(inspiration_item_id)
            if item is not None:
                await set_inspiration_used(item, True)

    await session.commit()
    return ContentIdeaOut.model_validate(idea)
