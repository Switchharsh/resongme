import json

import pytest

from resongme.backends.acestep import AceStepBackend
from resongme.backends.elevenlabs import MAX_SECTION_MS, MIN_SECTION_MS, composition_plan
from resongme.lyricist import _brief, _ensure_voice_tag
from resongme.pipeline import slugify
from resongme.resume import load_resume
from resongme.song import SongPlan, SongRequest

PLAN = {
    "title": "Ledger Legend",
    "style_tags": ["rap", "boom bap", "confident", "male vocals"],
    "bpm": 92,
    "key_scale": "A minor",
    "sections": [
        {"name": "intro", "lines": []},
        {"name": "verse", "lines": ["Line one", "Line two", "Line three", "Line four"]},
        {"name": "chorus", "lines": ["Hook one", "Hook two"]},
    ],
}


def plan(**kw):
    return SongPlan.from_dict(PLAN, duration_s=kw.get("duration_s", 120), language="en")


def test_lyrics_have_section_tags():
    lyrics = plan().lyrics()
    assert lyrics.startswith("[intro]\n\n[verse]\nLine one")
    assert "[chorus]\nHook one\nHook two" in lyrics


def test_requested_voice_replaces_model_vocal_tag():
    p = plan()
    _ensure_voice_tag(p, "female")
    assert p.style_tags == ["rap", "boom bap", "confident", "female vocals"]


def test_any_voice_keeps_tags():
    p = plan()
    _ensure_voice_tag(p, "any")
    assert "male vocals" in p.style_tags


def test_brief_mentions_genre_and_singer():
    brief = _brief(SongRequest(genre="rap", voice="male", mood="hype"))
    assert "Genre: rap" in brief and "male vocals" in brief and "Mood: hype" in brief


def test_acestep_payload():
    backend = AceStepBackend(base_url="http://example.invalid")
    payload = backend.payload(plan(), "mp3")
    assert payload["prompt"] == "rap, boom bap, confident, male vocals"
    assert payload["lyrics"].startswith("[intro]")
    assert payload["audio_duration"] == 120
    assert payload["bpm"] == 92 and payload["key_scale"] == "A minor"


def test_elevenlabs_plan_durations_within_limits():
    cp = composition_plan(plan(duration_s=600))
    assert [s["section_name"] for s in cp["sections"]] == ["intro", "verse", "chorus"]
    for s in cp["sections"]:
        assert MIN_SECTION_MS <= s["duration_ms"] <= MAX_SECTION_MS
    assert cp["sections"][0]["lines"] == []
    assert "92 bpm" in cp["positive_global_styles"]


def test_load_text_resume(tmp_path):
    f = tmp_path / "cv.txt"
    f.write_text("Jane Doe, engineer")
    blocks = load_resume(f)
    assert blocks[0]["type"] == "text" and "Jane Doe" in blocks[0]["text"]


def test_load_pdf_resume_is_native_document(tmp_path):
    f = tmp_path / "cv.pdf"
    f.write_bytes(b"%PDF-1.4 fake")
    block = load_resume(f)[0]
    assert block["type"] == "document"
    assert block["source"]["media_type"] == "application/pdf"


def test_unsupported_format(tmp_path):
    f = tmp_path / "cv.rtf"
    f.write_text("x")
    with pytest.raises(ValueError):
        load_resume(f)


def test_slugify():
    assert slugify("Ledger Legend (Remix)!") == "ledger-legend-remix"
    assert slugify("!!!") == "song"
