"""Resume -> lyrics (Claude) -> audio (backend)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .backends import get_backend
from .lyricist import write_song
from .resume import load_resume
from .song import SongPlan, SongRequest


@dataclass
class SongResult:
    plan: SongPlan
    lyrics_path: Path
    audio_path: Path | None


def make_song(
    resume_path: str | Path,
    request: SongRequest,
    backend: str = "acestep",
    out_dir: str | Path = "output",
    audio_format: str = "mp3",
) -> SongResult:
    plan = write_song(load_resume(resume_path), request)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = slugify(plan.title)
    lyrics_path = out_dir / f"{stem}.md"
    lyrics_path.write_text(plan.to_markdown(), encoding="utf-8")

    audio_path = get_backend(backend).render(plan, out_dir / f"{stem}.{audio_format}")
    return SongResult(plan, lyrics_path, audio_path)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "song"
