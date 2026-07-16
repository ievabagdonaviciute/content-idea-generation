"""Hardcoded, stable personal configuration for this single-user install.

Kadro is a personal tool, not a multi-tenant product. Values here are not secrets,
are not expected to change at runtime, and must never be requested through a setup
wizard, the UI, or the CLI. To change one, edit this file and restart the app.

The only Notion-related value that comes from the environment is ``NOTION_TOKEN``
(see ``app.core.config.Settings``) because it is a credential.
"""

from __future__ import annotations

# The Notion page that contains (or will contain) the inspiration database. Kadro
# extracts the page ID from this URL, finds or creates a child database named
# NOTION_INSPIRATION_DATABASE_TITLE inside it, and never asks for a database ID.
NOTION_PAGE_URL = "https://app.notion.com/p/Content-Inspo-39e4386daefa80779e82cc34b5796aaf"

# Name of the database Kadro looks for (or creates) inside NOTION_PAGE_URL.
NOTION_INSPIRATION_DATABASE_TITLE = "TikTok Inspiration"

# Default TikTok handle this install is about. Still editable afterwards through the
# Settings page (backed by the UserSettings table) -- this is only the seed value.
DEFAULT_TIKTOK_USERNAME = "ieva.bagdonaviciute"
