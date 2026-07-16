from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.repositories.own_content_repository import OwnContentRepository
from app.schemas.common import Page
from app.schemas.posts import OwnPostOut

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=Page[OwnPostOut])
async def list_posts(
    limit: int = 50, offset: int = 0, session: AsyncSession = Depends(get_session)
) -> Page[OwnPostOut]:
    repo = OwnContentRepository(session)
    posts = await repo.list_own_posts(limit=limit, offset=offset)
    return Page(
        items=[OwnPostOut.model_validate(post) for post in posts],
        total=len(posts),
        limit=limit,
        offset=offset,
    )


@router.get("/{post_id}", response_model=OwnPostOut)
async def get_post(post_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> OwnPostOut:
    repo = OwnContentRepository(session)
    post = await repo.get_own_post_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return OwnPostOut.model_validate(post)


@router.post("/{post_id}/reanalyze", response_model=OwnPostOut)
async def reanalyze_post(
    post_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> OwnPostOut:
    repo = OwnContentRepository(session)
    post = await repo.get_own_post_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    from app.pipelines.analysis_pipeline import run_own_post_analysis

    await run_own_post_analysis(session, post)
    await session.commit()
    post = await repo.get_own_post_by_id(post_id)
    assert post is not None
    return OwnPostOut.model_validate(post)
