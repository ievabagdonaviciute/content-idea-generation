from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.repositories.inspiration_repository import InspirationRepository
from app.schemas.common import Page
from app.schemas.inspiration import InspirationItemOut, SyncRunOut
from app.services.inspiration_usage import set_inspiration_used
from app.services.notion_sync import NotionSyncService

router = APIRouter(prefix="/inspiration", tags=["inspiration"])


@router.get("", response_model=Page[InspirationItemOut])
async def list_inspiration(
    limit: int = 50, offset: int = 0, session: AsyncSession = Depends(get_session)
) -> Page[InspirationItemOut]:
    repo = InspirationRepository(session)
    items = await repo.list_all(limit=limit, offset=offset)
    return Page(
        items=[InspirationItemOut.model_validate(item) for item in items],
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.post("/sync-notion", response_model=SyncRunOut)
async def sync_notion(session: AsyncSession = Depends(get_session)) -> SyncRunOut:
    service = NotionSyncService(session)
    sync_run = await service.sync()
    return SyncRunOut.model_validate(sync_run)


@router.get("/{item_id}", response_model=InspirationItemOut)
async def get_inspiration_item(
    item_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> InspirationItemOut:
    repo = InspirationRepository(session)
    item = await repo.get_by_id(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inspiration item not found")
    return InspirationItemOut.model_validate(item)


@router.post("/{item_id}/reanalyze", response_model=InspirationItemOut)
async def reanalyze_inspiration_item(
    item_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> InspirationItemOut:
    repo = InspirationRepository(session)
    item = await repo.get_by_id(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inspiration item not found")
    from app.pipelines.analysis_pipeline import run_inspiration_analysis

    await run_inspiration_analysis(session, item)
    await session.commit()
    return InspirationItemOut.model_validate(item)


async def _set_already_used(
    session: AsyncSession, item_id: uuid.UUID, value: bool
) -> InspirationItemOut:
    repo = InspirationRepository(session)
    item = await repo.get_by_id(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inspiration item not found")
    await set_inspiration_used(item, value)
    await session.commit()
    return InspirationItemOut.model_validate(item)


@router.post("/{item_id}/mark-used", response_model=InspirationItemOut)
async def mark_inspiration_item_used(
    item_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> InspirationItemOut:
    return await _set_already_used(session, item_id, True)


@router.post("/{item_id}/unmark-used", response_model=InspirationItemOut)
async def unmark_inspiration_item_used(
    item_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> InspirationItemOut:
    return await _set_already_used(session, item_id, False)
