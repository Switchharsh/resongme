from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..song import SongPlan


class AudioBackend(Protocol):
    name: str

    def render(self, plan: SongPlan, out_path: Path) -> Path | None:
        """Generate audio for the plan; return the written file (or None if no audio)."""
        ...


class LyricsOnlyBackend:
    name = "none"

    def render(self, plan: SongPlan, out_path: Path) -> Path | None:
        return None
