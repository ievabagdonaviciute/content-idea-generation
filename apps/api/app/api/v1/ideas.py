from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.idea import FEEDBACK_RATINGS
from app.repositories.idea_repository import IdeaRepository
from app.schemas.common import Page
from app.schemas.ideas import (
    ContentIdeaOut,
    GeneratedBriefOut,
    GeneratedScriptOut,
    IdeaFeedbackRequest,
    IdeaGenerateRequest,
    ScriptGenerateRequest,
)
from app.services.brief_generation import generate_brief
from app.services.idea_generation import IdeaGenerationRequest, generate_ideas
from app.services.script_generation import InvalidScriptModeError, generate_script

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.post("/generate", response_model=list[ContentIdeaOut])
async def generate_ideas_endpoint(
    body: IdeaGenerateRequest, session: AsyncSession = Depends(get_session)
) -> list[ContentIdeaOut]:
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
    await session.commit()
    return [ContentIdeaOut.model_validate(idea) for idea in ideas]


@router.get("", response_model=Page[ContentIdeaOut])
async def list_ideas(
    limit: int = 50, offset: int = 0, session: AsyncSession = Depends(get_session)
) -> Page[ContentIdeaOut]:
    repo = IdeaRepository(session)
    ideas = await repo.list_all(limit=limit, offset=offset)
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
    brief = await generate_brief(session, idea)
    await session.commit()
    return GeneratedBriefOut.model_validate(brief)


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
    await session.commit()
    return GeneratedScriptOut.model_validate(script)
