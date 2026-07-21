from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.ideas import router as ideas_router
from app.api.v1.inspiration import router as inspiration_router
from app.api.v1.posts import router as posts_router
from app.api.v1.profile import router as profile_router
from app.api.v1.sync import router as sync_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(inspiration_router)
api_router.include_router(posts_router)
api_router.include_router(sync_router)
api_router.include_router(ideas_router)
api_router.include_router(profile_router)
