"""The Notion database schema Kadro auto-provisions and verifies.

See docs/NOTION_SETUP.md. Property names here are the source of truth; the Notion
sync client and mock adapter both key off of these constants instead of repeating
literal strings.
"""

from __future__ import annotations

from typing import Any

PROP_TITLE = "Title"
PROP_URL = "TikTok URL"
PROP_STATUS = "Status"
PROP_ADDED = "Added"
PROP_CREATOR = "Creator"
PROP_TOPIC = "Topic"
PROP_FORMAT = "Format"
PROP_WHY_SAVED = "Why I saved it"
PROP_FAVORITE_PART = "My favorite part"
PROP_PROCESSING_ERROR = "Processing Error"
PROP_PROCESSED_AT = "Processed At"

STATUS_OPTIONS = ["New", "Processing", "Processed", "Failed"]

_STATUS_COLORS = {"New": "blue", "Processing": "yellow", "Processed": "green", "Failed": "red"}


def _select_property(options: list[str]) -> dict[str, Any]:
    return {"select": {"options": [{"name": name} for name in options]}}


def _status_select_property() -> dict[str, Any]:
    return {
        "select": {
            "options": [{"name": name, "color": _STATUS_COLORS[name]} for name in STATUS_OPTIONS]
        }
    }


def required_database_properties() -> dict[str, dict[str, Any]]:
    """The full property schema, keyed by property name, in Notion API shape.

    Used both to create the database from scratch and to diff against an existing
    database's properties so only missing ones get added.
    """

    return {
        PROP_TITLE: {"title": {}},
        PROP_URL: {"url": {}},
        PROP_STATUS: _status_select_property(),
        PROP_ADDED: {"created_time": {}},
        PROP_CREATOR: {"rich_text": {}},
        PROP_TOPIC: {"multi_select": {"options": []}},
        PROP_FORMAT: _select_property([]),
        PROP_WHY_SAVED: {"rich_text": {}},
        PROP_FAVORITE_PART: {"rich_text": {}},
        PROP_PROCESSING_ERROR: {"rich_text": {}},
        PROP_PROCESSED_AT: {"date": {}},
    }


def missing_properties(existing: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Properties from the required schema not present in ``existing`` (a Notion
    database object's ``properties`` mapping)."""
    required = required_database_properties()
    return {name: schema for name, schema in required.items() if name not in existing}
