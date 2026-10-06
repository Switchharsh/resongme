"""Cloud backend: ElevenLabs Music (`pip install resongme[elevenlabs]`, set ELEVENLABS_API_KEY)."""

from __future__ import annotations

import os
from pathlib import Path

from ..song import SongPlan

MIN_SECTION_MS, MAX_SECTION_MS = 3_000, 120_000
MAX_LINE_CHARS, MAX_LINES = 200, 30
INSTRUMENTAL_WEIGHT = 2  # an instrumental section is sized like ~2 sung lines


class ElevenLabsBackend:
    name = "elevenlabs"

    def __init__(self, api_key: str | None = None, model_id: str = "music_v1"):
        from elevenlabs import ElevenLabs

        key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not key:
            raise RuntimeError("Set ELEVENLABS_API_KEY to use the elevenlabs backend.")
        self.client = ElevenLabs(api_key=key)
        self.model_id = model_id

    def render(self, plan: SongPlan, out_path: Path) -> Path:
        audio = self.client.music.compose(
            composition_plan=composition_plan(plan),
            model_id=self.model_id,
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        return out_path


def composition_plan(plan: SongPlan) -> dict:
    """Map our song plan onto ElevenLabs' composition plan, splitting the target
    duration across sections in proportion to their line counts."""
    weights = [len(s.lines) or INSTRUMENTAL_WEIGHT for s in plan.sections]
    total_ms = plan.duration_s * 1000
    total_w = sum(weights) or 1

    sections = []
    for s, w in zip(plan.sections, weights):
        ms = round(total_ms * w / total_w)
        sections.append(
            {
                "section_name": s.name[:100],
                "positive_local_styles": [s.name],
                "negative_local_styles": [],
                "duration_ms": min(max(ms, MIN_SECTION_MS), MAX_SECTION_MS),
                "lines": [line[:MAX_LINE_CHARS] for line in s.lines[:MAX_LINES]],
            }
        )
    return {
        "positive_global_styles": plan.style_tags + [f"{plan.bpm} bpm", plan.key_scale],
        "negative_global_styles": [],
        "sections": sections,
    }
