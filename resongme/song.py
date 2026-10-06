"""Song request/plan data types shared by the lyricist and the audio backends."""

from __future__ import annotations

from dataclasses import dataclass, field

GENRES = (
    "pop", "rap", "hip-hop", "rock", "country", "r&b", "edm", "jazz",
    "metal", "folk", "reggae", "k-pop", "lo-fi", "musical theatre",
)
VOICES = ("male", "female", "duet", "choir", "any")


@dataclass
class SongRequest:
    genre: str = "pop"
    voice: str = "female"
    mood: str = ""
    duration_s: int = 150
    language: str = "en"
    extra: str = ""  # free-form direction, e.g. "make it about landing my first job"


@dataclass
class Section:
    name: str  # verse, chorus, bridge, intro, outro, pre-chorus, hook
    lines: list[str]


@dataclass
class SongPlan:
    title: str
    style_tags: list[str]
    bpm: int
    key_scale: str
    sections: list[Section] = field(default_factory=list)
    duration_s: int = 150
    language: str = "en"

    @classmethod
    def from_dict(cls, data: dict, *, duration_s: int, language: str) -> "SongPlan":
        return cls(
            title=data["title"],
            style_tags=list(data["style_tags"]),
            bpm=int(data["bpm"]),
            key_scale=data["key_scale"],
            sections=[Section(s["name"], list(s["lines"])) for s in data["sections"]],
            duration_s=duration_s,
            language=language,
        )

    def caption(self) -> str:
        """Comma-separated style description used as the music model's prompt."""
        return ", ".join(self.style_tags)

    def lyrics(self) -> str:
        """Lyrics with [section] tags, the format ACE-Step and most music models expect."""
        blocks = []
        for s in self.sections:
            body = "\n".join(s.lines)
            blocks.append(f"[{s.name}]\n{body}" if body else f"[{s.name}]")
        return "\n\n".join(blocks)

    def to_markdown(self) -> str:
        return (
            f"# {self.title}\n\n"
            f"*Style:* {self.caption()}  \n"
            f"*BPM:* {self.bpm} · *Key:* {self.key_scale} · *Length:* ~{self.duration_s}s\n\n"
            f"```\n{self.lyrics()}\n```\n"
        )


def voice_tag(voice: str) -> str:
    return {
        "male": "male vocals",
        "female": "female vocals",
        "duet": "male and female duet vocals",
        "choir": "choir vocals",
    }.get(voice.lower(), "")
