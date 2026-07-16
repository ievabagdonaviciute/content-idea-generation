from __future__ import annotations

import pytest

from app.core.url_validation import InvalidTikTokUrlError, extract_video_id, normalize_tiktok_url


def test_normalize_strips_query_string() -> None:
    a = normalize_tiktok_url(
        "https://www.tiktok.com/@someone/video/123456?is_from_webapp=1&sender_device=pc"
    )
    b = normalize_tiktok_url("https://www.tiktok.com/@someone/video/123456")
    assert a == b


def test_normalize_lowercases_host() -> None:
    result = normalize_tiktok_url("https://WWW.TikTok.com/@someone/video/123456")
    assert result == "https://www.tiktok.com/@someone/video/123456"


def test_normalize_strips_trailing_slash() -> None:
    assert normalize_tiktok_url(
        "https://www.tiktok.com/@someone/video/123456/"
    ) == normalize_tiktok_url("https://www.tiktok.com/@someone/video/123456")


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example.com/@someone/video/123456",
        "https://tiktok.com.evil.com/video/123",
        "ftp://www.tiktok.com/@someone/video/123456",
        "",
        "not a url",
    ],
)
def test_normalize_rejects_disallowed_hosts_and_schemes(url: str) -> None:
    with pytest.raises(InvalidTikTokUrlError):
        normalize_tiktok_url(url)


def test_normalize_allows_short_link_hosts() -> None:
    result = normalize_tiktok_url("https://vm.tiktok.com/ZMabc123/")
    assert result == "https://vm.tiktok.com/ZMabc123"


def test_extract_video_id_present() -> None:
    video_id = extract_video_id("https://www.tiktok.com/@someone/video/7301000000000000001")
    assert video_id == "7301000000000000001"


def test_extract_video_id_absent_for_short_link() -> None:
    assert extract_video_id("https://vm.tiktok.com/ZMabc123") is None
