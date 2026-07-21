from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.idea import ContentIdea, IdeaFeedback


class IdeaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _with_relations(self) -> Select[tuple[ContentIdea]]:
        return select(ContentIdea).options(
            selectinload(ContentIdea.sources),
            selectinload(ContentIdea.feedback_entries),
            selectinload(ContentIdea.brief),
            selectinload(ContentIdea.script),
        )

    async def get_by_id(self, idea_id: uuid.UUID) -> ContentIdea | None:
        result = await self._session.execute(
            self._with_relations().where(ContentIdea.id == idea_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, limit: int = 50, offset: int = 0) -> list[ContentIdea]:
        result = await self._session.execute(
            self._with_relations()
            .order_by(ContentIdea.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    def add(self, idea: ContentIdea) -> None:
        self._session.add(idea)

    async def add_feedback(
        self, idea: ContentIdea, rating: str, comment: str | None
    ) -> IdeaFeedback:
        # Appending to idea.feedback_entries (rather than setting idea_id and
        # session.add() separately) keeps the already-loaded ``idea`` object's
        # relationship in sync in memory immediately -- see the identical fix
        # in app/pipelines/analysis_pipeline.py.
        feedback = IdeaFeedback(rating=rating, comment=comment)
        idea.feedback_entries.append(feedback)
        await self._session.flush()
        return feedback
