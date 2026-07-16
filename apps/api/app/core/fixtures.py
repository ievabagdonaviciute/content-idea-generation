"""Loads JSON fixtures from the repo-root ``fixtures/`` directory.

Shared by the mock Notion client, the mock TikTok provider, and the seed CLI command
so there is exactly one place that knows where fixture files live.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parents[4] / "fixtures"


@lru_cache
def load_fixture(name: str) -> Any:
    path = FIXTURES_DIR / name
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)
