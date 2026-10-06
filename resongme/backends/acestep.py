"""Local backend: ACE-Step 1.5 REST API (https://github.com/ACE-Step/ACE-Step-1.5).

Start the server in the ACE-Step repo with `uv run acestep-api` (default port 8001).
API reference: docs/en/API.md in that repo.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx

from ..song import SongPlan

STATUS_RUNNING, STATUS_OK, STATUS_FAILED = 0, 1, 2


class AceStepError(RuntimeError):
    pass


class AceStepBackend:
    name = "acestep"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_s: float = 900,
        poll_s: float = 2.0,
        thinking: bool = True,
    ):
        self.base_url = (base_url or os.getenv("ACESTEP_URL") or "http://localhost:8001").rstrip("/")
        api_key = api_key or os.getenv("ACESTEP_API_KEY") or None
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.http = httpx.Client(base_url=self.base_url, headers=headers, timeout=60)
        self.timeout_s = timeout_s
        self.poll_s = poll_s
        self.thinking = thinking

    def payload(self, plan: SongPlan, audio_format: str) -> dict:
        return {
            "prompt": plan.caption(),
            "lyrics": plan.lyrics(),
            "vocal_language": plan.language,
            "audio_duration": plan.duration_s,
            "bpm": plan.bpm,
            "key_scale": plan.key_scale,
            "time_signature": "4",
            # Let ACE-Step's 5Hz LM plan the audio codes (better structure/quality),
            # but keep our caption and language instead of having it rewrite them.
            "thinking": self.thinking,
            "use_cot_caption": False,
            "use_cot_language": False,
            "batch_size": 1,
            "audio_format": audio_format,
        }

    def render(self, plan: SongPlan, out_path: Path) -> Path:
        self._check_health()
        audio_format = out_path.suffix.lstrip(".").lower() or "mp3"

        task_id = self._unwrap(self.http.post("/release_task", json=self.payload(plan, audio_format)))["task_id"]
        result = self._wait(task_id)

        file_url = result["file"]
        resp = self.http.get(file_url, timeout=120)
        resp.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(resp.content)
        return out_path

    def _check_health(self) -> None:
        try:
            self.http.get("/health", timeout=5).raise_for_status()
        except httpx.HTTPError as e:
            raise AceStepError(
                f"ACE-Step server not reachable at {self.base_url} ({e}). "
                "Start it with `uv run acestep-api` in the ACE-Step-1.5 repo, or set ACESTEP_URL."
            ) from e

    def _wait(self, task_id: str) -> dict:
        deadline = time.monotonic() + self.timeout_s
        while time.monotonic() < deadline:
            items = self._unwrap(self.http.post("/query_result", json={"task_id_list": [task_id]}))
            item = next((i for i in items if i.get("task_id") == task_id), None)
            if item and item.get("status") == STATUS_OK:
                results = json.loads(item["result"]) if isinstance(item["result"], str) else item["result"]
                ok = [r for r in results if r.get("status", STATUS_OK) == STATUS_OK and r.get("file")]
                if not ok:
                    raise AceStepError(f"ACE-Step task {task_id} finished without audio: {results}")
                return ok[0]
            if item and item.get("status") == STATUS_FAILED:
                raise AceStepError(f"ACE-Step task {task_id} failed: {item.get('result')}")
            time.sleep(self.poll_s)
        raise AceStepError(f"ACE-Step task {task_id} timed out after {self.timeout_s}s")

    @staticmethod
    def _unwrap(resp: httpx.Response):
        resp.raise_for_status()
        body = resp.json()
        if body.get("code") != 200 or body.get("error"):
            raise AceStepError(f"ACE-Step error: {body.get('error') or body}")
        return body["data"]
