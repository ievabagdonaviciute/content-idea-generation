"""Deterministic fake image/meme providers, used when PEXELS_API_KEY /
IMGFLIP_USERNAME+PASSWORD are not configured -- see app/integrations/media/base.py.
Never makes a network call: URLs are constructed strings pointing at a public
placeholder-image service (picsum.photos), seeded from the input so the same query
always returns the same set, matching the determinism of app/ai/fake_providers.py.
"""

from __future__ import annotations

import hashlib

from app.integrations.media.base import ImageResult, MemeResult, MemeTemplate

_FAKE_TEMPLATE_NAMES = (
    "Drake Hotline Bling",
    "Distracted Boyfriend",
    "Two Buttons",
    "Change My Mind",
    "Expanding Brain",
)


def _seed(*parts: str) -> int:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


class FakeImageSearchProvider:
    async def search(self, query: str, count: int) -> list[ImageResult]:
        results = []
        for i in range(count):
            seed = _seed(query, str(i))
            results.append(
                ImageResult(
                    url=f"https://picsum.photos/seed/{seed}/800/600",
                    thumbnail_url=f"https://picsum.photos/seed/{seed}/200/150",
                    source_url=f"https://picsum.photos/seed/{seed}",
                    credit="Fake placeholder image (no PEXELS_API_KEY configured)",
                )
            )
        return results


class FakeMemeProvider:
    async def list_templates(self, count: int) -> list[MemeTemplate]:
        return [
            MemeTemplate(
                template_id=f"fake-{i}",
                name=_FAKE_TEMPLATE_NAMES[i % len(_FAKE_TEMPLATE_NAMES)],
                box_count=2,
            )
            for i in range(count)
        ]

    async def caption(self, template: MemeTemplate, lines: list[str]) -> MemeResult:
        seed = _seed(template.template_id, *lines)
        return MemeResult(
            url=f"https://picsum.photos/seed/{seed}/500/500",
            template_name=template.name,
            caption_lines=lines,
        )
