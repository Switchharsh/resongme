import json

import httpx

from resongme.backends.acestep import AceStepBackend
from resongme.song import Section, SongPlan


def wrap(data):
    return {"data": data, "code": 200, "error": None, "timestamp": 0, "extra": None}


def test_render_polls_and_downloads(tmp_path):
    calls = {"query": 0}

    def handler(request: httpx.Request):
        if request.url.path == "/health":
            return httpx.Response(200, json=wrap({"status": "ok"}))
        if request.url.path == "/release_task":
            body = json.loads(request.content)
            assert body["lyrics"] == "[chorus]\nla la"
            return httpx.Response(200, json=wrap({"task_id": "t1", "status": "queued"}))
        if request.url.path == "/query_result":
            calls["query"] += 1
            if calls["query"] == 1:
                return httpx.Response(200, json=wrap([{"task_id": "t1", "status": 0, "result": "[]"}]))
            result = json.dumps([{"file": "/v1/audio?path=%2Ftmp%2Fa.mp3", "status": 1}])
            return httpx.Response(200, json=wrap([{"task_id": "t1", "status": 1, "result": result}]))
        if request.url.path == "/v1/audio":
            return httpx.Response(200, content=b"ID3fake")
        return httpx.Response(404)

    backend = AceStepBackend(base_url="http://ace.test", poll_s=0)
    backend.http = httpx.Client(base_url="http://ace.test", transport=httpx.MockTransport(handler))
    plan = SongPlan("t", ["pop"], 120, "C Major", [Section("chorus", ["la la"])], duration_s=30)

    out = backend.render(plan, tmp_path / "song.mp3")
    assert out.read_bytes() == b"ID3fake"
    assert calls["query"] == 2
