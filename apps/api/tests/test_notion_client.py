from __future__ import annotations

from app.core.personal_config import NOTION_PAGE_URL
from app.integrations.notion.client import parse_notion_page
from app.integrations.notion.page_url import extract_page_id
from app.integrations.notion.schema import missing_properties, required_database_properties


def test_extract_page_id_from_hardcoded_page_url() -> None:
    page_id = extract_page_id(NOTION_PAGE_URL)
    assert page_id == "39e4386d-aefa-8077-9e82-cc34b5796aaf"


def test_extract_page_id_from_legacy_notion_so_url() -> None:
    page_id = extract_page_id("https://www.notion.so/My-Page-39e4386daefa80779e82cc34b5796aaf")
    assert page_id == "39e4386d-aefa-8077-9e82-cc34b5796aaf"


_SAMPLE_NOTION_PAGE = {
    "id": "page-abc-123",
    "properties": {
        "Title": {"title": [{"plain_text": "Great hook idea"}]},
        "TikTok URL": {"url": "https://www.tiktok.com/@someone/video/123"},
        "Creator": {"rich_text": [{"plain_text": "someone"}]},
        "Topic": {"multi_select": [{"name": "AI"}, {"name": "etika"}]},
        "Format": {"select": {"name": "grwm_story"}},
        "Why I saved it": {"rich_text": [{"plain_text": "Patiko hook'as."}]},
        "My favorite part": {"rich_text": []},
        "Status": {"select": {"name": "New"}},
        "Added": {"created_time": "2026-05-01T10:00:00.000Z"},
    },
}


def test_parse_notion_page_extracts_all_fields() -> None:
    row = parse_notion_page(_SAMPLE_NOTION_PAGE)
    assert row.notion_page_id == "page-abc-123"
    assert row.title == "Great hook idea"
    assert row.tiktok_url == "https://www.tiktok.com/@someone/video/123"
    assert row.creator == "someone"
    assert row.topics == ["AI", "etika"]
    assert row.format_hint == "grwm_story"
    assert row.note_why_saved == "Patiko hook'as."
    assert row.note_favorite_part is None
    assert row.status == "New"
    assert row.added_at is not None


def test_missing_properties_detects_gaps() -> None:
    existing = {"Title": {"title": {}}, "TikTok URL": {"url": {}}}
    missing = missing_properties(existing)
    assert "Title" not in missing
    assert "TikTok URL" not in missing
    assert "Status" in missing
    assert "Processing Error" in missing
    assert set(missing) == set(required_database_properties()) - set(existing)


def test_missing_properties_empty_when_schema_complete() -> None:
    existing = required_database_properties()
    assert missing_properties(existing) == {}
