"""Interfaces for sourcing images and memes relevant to a ContentIdea, so a
creator can pull production-ready visuals for editing without leaving Kadro. See
docs/MEDIA_SOURCING.md.

Never scrapes or bypasses access controls -- ``ImageSearchProvider`` talks to the
official Pexels search API, and ``MemeProvider`` talks to the official Imgflip
captioning API. Both require real credentials (see docs/MEDIA_SOURCING.md); a fake
implementation runs by default so the feature is exercisable and testable without
either.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ImageResult:
    url: str
    thumbnail_url: str
    source_url: str
    credit: str | None = None


@dataclass
class MemeTemplate:
    template_id: str
    name: str
    box_count: int


@dataclass
class MemeResult:
    url: str
    template_name: str
    caption_lines: list[str]


class ImageSearchProvider(Protocol):
    async def search(self, query: str, count: int) -> list[ImageResult]: ...


class MemeProvider(Protocol):
    async def list_templates(self, count: int) -> list[MemeTemplate]: ...

    async def caption(self, template: MemeTemplate, lines: list[str]) -> MemeResult: ...
