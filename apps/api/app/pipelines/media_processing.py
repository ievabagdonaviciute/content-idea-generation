"""FFmpeg-backed media processing: audio extraction and representative-frame
sampling. Always invoked via ``asyncio.create_subprocess_exec`` with an explicit
argument list -- never a shell string -- so there is no shell interpolation
regardless of what a filename contains. See docs/PRIVACY_AND_SECURITY.md.
"""

from __future__ import annotations

import asyncio
from pathlib import Path


class MediaProcessingError(RuntimeError):
    pass


async def _run(*argv: str) -> str:
    process = await asyncio.create_subprocess_exec(
        *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise MediaProcessingError(
            f"{argv[0]} failed (exit {process.returncode}): {stderr.decode(errors='ignore')[:500]}"
        )
    return stdout.decode(errors="ignore")


async def probe_duration_seconds(video_path: Path) -> float:
    output = await _run(
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    )
    return float(output.strip())


async def extract_audio(video_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    await _run("ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "aac", str(output_path))
    return output_path


async def sample_frames(video_path: Path, output_dir: Path, max_frames: int) -> list[Path]:
    """Evenly-spaced frame extraction, capped at ``max_frames``."""
    duration = await probe_duration_seconds(video_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    frame_paths: list[Path] = []
    for i in range(max_frames):
        timestamp = duration * (i + 1) / (max_frames + 1)
        frame_path = output_dir / f"frame_{i:02d}.jpg"
        await _run(
            "ffmpeg",
            "-y",
            "-ss",
            f"{timestamp:.2f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            str(frame_path),
        )
        frame_paths.append(frame_path)
    return frame_paths
