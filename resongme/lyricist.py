"""Claude reads the resume and writes a structured song plan."""

from __future__ import annotations

import json

import anthropic

from .song import SongPlan, SongRequest, voice_tag

MODEL = "claude-opus-5-5"

SYSTEM = """You are a professional songwriter. You turn a person's resume into an \
original song that celebrates them: their name, roles, companies, skills, projects, \
wins and journey. Write concrete, specific, singable lyrics - real details from the \
resume, not generic career platitudes - with strong rhyme, rhythm and a memorable hook \
that fits the requested genre's conventions (e.g. dense internal rhymes and flow for \
rap, a big repeated chorus for pop, storytelling for country).

Keep it positive and fun. Do not include contact details (email, phone, street \
address) in the lyrics. Write original lyrics; do not quote existing songs.

style_tags are fed straight to a text-to-music model: give 5-10 short English tags \
covering genre, sub-genre, mood, key instruments, production style and the vocal type \
(e.g. "female vocals"). Section names must be one of: intro, verse, pre-chorus, \
chorus, hook, bridge, outro. Instrumental sections have an empty lines list. Size the \
lyrics so they can be performed in roughly the requested length."""

SONG_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "style_tags": {"type": "array", "items": {"type": "string"}},
        "bpm": {"type": "integer"},
        "key_scale": {"type": "string", "description": 'e.g. "C Major", "A minor"'},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "lines": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "lines"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "style_tags", "bpm", "key_scale", "sections"],
    "additionalProperties": False,
}


class LyricsError(RuntimeError):
    pass


def write_song(
    resume_blocks: list[dict],
    request: SongRequest,
    client: anthropic.Anthropic | None = None,
) -> SongPlan:
    client = client or anthropic.Anthropic()
    brief = _brief(request)

    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": SONG_SCHEMA},
        },
        # Server-side fallback re-runs a safety-declined request on another model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": [*resume_blocks, {"type": "text", "text": brief}]}],
    )

    if response.stop_reason == "refusal":
        reason = response.stop_details.explanation if response.stop_details else "no details"
        raise LyricsError(f"Claude declined to write this song: {reason}")
    if response.stop_reason == "max_tokens":
        raise LyricsError("Lyrics were cut off (max_tokens); try a shorter duration.")

    text = "".join(b.text for b in response.content if b.type == "text")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise LyricsError(f"Could not parse song plan from Claude: {e}") from e

    plan = SongPlan.from_dict(data, duration_s=request.duration_s, language=request.language)
    _ensure_voice_tag(plan, request.voice)
    return plan


def _brief(r: SongRequest) -> str:
    lines = [
        "Write a song about the person in this resume.",
        f"Genre: {r.genre}",
        f"Singer: {voice_tag(r.voice) or 'any voice'}",
        f"Target length: about {r.duration_s} seconds",
        f"Lyrics language: {r.language}",
    ]
    if r.mood:
        lines.append(f"Mood: {r.mood}")
    if r.extra:
        lines.append(f"Extra direction: {r.extra}")
    return "\n".join(lines)


def _ensure_voice_tag(plan: SongPlan, voice: str) -> None:
    """The singer's gender is the one tag the user explicitly asked for - guarantee it."""
    tag = voice_tag(voice)
    if tag:
        plan.style_tags = [t for t in plan.style_tags if "vocal" not in t.lower()] + [tag]
