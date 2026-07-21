from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.profile import ContentProfileSnapshotOut
from app.services.profile import build_profile_snapshot, get_latest_profile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ContentProfileSnapshotOut)
async def get_profile(session: AsyncSession = Depends(get_session)) -> ContentProfileSnapshotOut:
    profile = await get_latest_profile(session)
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile has been built yet")
    return ContentProfileSnapshotOut.model_validate(profile)


@router.post("/rebuild", response_model=ContentProfileSnapshotOut)
async def rebuild_profile(
    session: AsyncSession = Depends(get_session),
) -> ContentProfileSnapshotOut:
    profile = await build_profile_snapshot(session)
    await session.commit()
    return ContentProfileSnapshotOut.model_validate(profile)
