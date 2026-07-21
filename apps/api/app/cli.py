"""Kadro command-line entry points. Run with ``python -m app.cli <command>``.

The DB-manipulating core of ``seed`` and ``purge-local-data`` lives in
module-level functions (``seed_reference_data``, ``purge_database_rows``,
``purge_media_storage``) so they're directly testable against the
``db_session`` fixture, independent of the Typer command wiring.
"""

from __future__ import annotations

import asyncio
import shutil

import typer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.db.seed_data import CONTENT_FORMATS
from app.models import Base
from app.models.content_format import ContentFormat
from app.models.user_settings import UserSettings

cli = typer.Typer(help="Kadro backend CLI")
logger = get_logger(__name__)


@cli.command("sync-notion")
def sync_notion() -> None:
    """Sync New rows from the Notion inspiration database."""

    async def _run() -> None:
        from app.db.session import get_session_factory
        from app.services.notion_sync import NotionSyncService

        session_factory = get_session_factory()
        async with session_factory() as session:
            service = NotionSyncService(session)
            sync_run = await service.sync()
            typer.echo(
                f"Notion sync complete: processed={sync_run.items_processed} "
                f"failed={sync_run.items_failed} status={sync_run.status}"
            )

    configure_logging(get_settings().app_env)
    asyncio.run(_run())


@cli.command("sync-tiktok")
def sync_tiktok() -> None:
    """Sync the creator's own TikTok posts."""

    async def _run() -> None:
        from app.db.session import get_session_factory
        from app.services.tiktok_sync import TikTokSyncService

        session_factory = get_session_factory()
        async with session_factory() as session:
            service = TikTokSyncService(session)
            sync_run = await service.sync()
            typer.echo(
                f"TikTok sync complete: processed={sync_run.items_processed} "
                f"status={sync_run.status}"
                + (f" error={sync_run.error_summary}" if sync_run.error_summary else "")
            )

    configure_logging(get_settings().app_env)
    asyncio.run(_run())


async def seed_reference_data(session: AsyncSession, settings: Settings) -> tuple[int, bool]:
    """Insert missing ContentFormat rows and the singleton UserSettings row.
    Safe to call repeatedly. Returns (formats created, settings created)."""
    existing_codes = set((await session.execute(select(ContentFormat.code))).scalars().all())
    created_formats = 0
    for fmt in CONTENT_FORMATS:
        if fmt["code"] not in existing_codes:
            session.add(ContentFormat(**fmt))
            created_formats += 1

    existing_settings = (await session.execute(select(UserSettings))).scalar_one_or_none()
    created_settings = existing_settings is None
    if created_settings:
        session.add(UserSettings(tiktok_username=settings.default_tiktok_username))

    await session.commit()
    return created_formats, created_settings


@cli.command("seed")
def seed() -> None:
    """Insert reference content-format rows and the singleton UserSettings row
    if they don't already exist. Safe to run repeatedly."""

    async def _run() -> None:
        from app.db.session import get_session_factory

        settings = get_settings()
        session_factory = get_session_factory()
        async with session_factory() as session:
            created_formats, created_settings = await seed_reference_data(session, settings)
            typer.echo(
                f"Seed complete: {created_formats} content format(s) added, "
                f"user settings {'created' if created_settings else 'already existed'}."
            )

    configure_logging(get_settings().app_env)
    asyncio.run(_run())


async def purge_database_rows(session: AsyncSession) -> None:
    """Delete every row from every table, in reverse-FK-dependency order."""
    for table in reversed(Base.metadata.sorted_tables):
        await session.execute(table.delete())
    await session.commit()


def purge_media_storage(settings: Settings) -> None:
    """Remove everything under MEDIA_STORAGE_PATH."""
    media_dir = settings.media_storage_dir
    if not media_dir.exists():
        return
    for child in media_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


@cli.command("purge-local-data")
def purge_local_data(
    yes: bool = typer.Option(False, "--yes", help="Skip the confirmation prompt."),
) -> None:
    """Delete all locally stored personal data: every database row and
    everything under MEDIA_STORAGE_PATH. Never touches your Notion database or
    TikTok account -- those are the systems of record you control directly.
    See docs/PRIVACY_AND_SECURITY.md."""

    if not yes:
        confirmed = typer.confirm(
            "This will permanently delete all local Kadro data (database rows and "
            "stored media). Continue?"
        )
        if not confirmed:
            typer.echo("Aborted.")
            raise typer.Exit(code=1)

    async def _run() -> None:
        from app.db.session import get_session_factory

        settings = get_settings()
        session_factory = get_session_factory()
        async with session_factory() as session:
            await purge_database_rows(session)
        purge_media_storage(settings)
        typer.echo("All local Kadro data has been deleted.")

    configure_logging(get_settings().app_env)
    asyncio.run(_run())


if __name__ == "__main__":
    cli()
