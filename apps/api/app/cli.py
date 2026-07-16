"""Kadro command-line entry points. Run with ``python -m app.cli <command>``."""

from __future__ import annotations

import asyncio

import typer

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

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


if __name__ == "__main__":
    cli()
