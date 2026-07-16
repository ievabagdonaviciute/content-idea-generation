from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.sync_run import SyncRun
from app.schemas.common import Page
from app.schemas.inspiration import SyncRunOut
from app.services.tiktok_sync import TikTokSyncService

router = APIRouter(tags=["sync"])


@router.post("/sync/tiktok", response_model=SyncRunOut)
async def sync_tiktok(session: AsyncSession = Depends(get_session)) -> SyncRunOut:
    service = TikTokSyncService(session)
    sync_run = await service.sync()
    return SyncRunOut.model_validate(sync_run)


@router.get("/sync-runs", response_model=Page[SyncRunOut])
async def list_sync_runs(
    limit: int = 50, offset: int = 0, session: AsyncSession = Depends(get_session)
) -> Page[SyncRunOut]:
    result = await session.execute(
        select(SyncRun).order_by(SyncRun.created_at.desc()).limit(limit).offset(offset)
    )
    runs = list(result.scalars().all())
    return Page(
        items=[SyncRunOut.model_validate(run) for run in runs],
        total=len(runs),
        limit=limit,
        offset=offset,
    )
