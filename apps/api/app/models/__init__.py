"""SQLAlchemy models. Import every module here so ``Base.metadata`` sees all tables
(used by ``Base.metadata.create_all`` in tests and by Alembic's autogenerate)."""

from app.db.base import Base
from app.models.content_analysis import ContentAnalysis
from app.models.content_format import ContentFormat
from app.models.content_profile_snapshot import ContentProfileSnapshot
from app.models.creator_profile import CreatorProfile
from app.models.external_account import ExternalAccount
from app.models.idea import (
    ContentIdea,
    GeneratedBrief,
    GeneratedScript,
    IdeaFeedback,
    IdeaSource,
    IdeaSourcedMedia,
)
from app.models.inspiration import InspirationItem
from app.models.media import MediaAsset
from app.models.own_post import OwnPost
from app.models.processing_job import ProcessingJob
from app.models.source_video import SourceVideo
from app.models.sync_run import SyncRun
from app.models.transcript import Transcript
from app.models.user_settings import UserSettings

__all__ = [
    "Base",
    "ContentAnalysis",
    "ContentFormat",
    "ContentProfileSnapshot",
    "CreatorProfile",
    "ExternalAccount",
    "ContentIdea",
    "GeneratedBrief",
    "GeneratedScript",
    "IdeaFeedback",
    "IdeaSource",
    "IdeaSourcedMedia",
    "InspirationItem",
    "MediaAsset",
    "OwnPost",
    "ProcessingJob",
    "SourceVideo",
    "SyncRun",
    "Transcript",
    "UserSettings",
]
