# 🎤 ResongMe

Give it your resume, pick a genre and a singer, and get back a full song about you,
with vocals.

```
resume.pdf ──► Claude (writes the lyrics, style tags, BPM, key) ──► music model (sings it) ──► song.mp3
```

## Which audio API? Can it run locally?

Yes. The default backend runs entirely on your own machine.

| Backend | Where it runs | Cost | Quality | Notes |
|---|---|---|---|---|
| **`acestep`** (default): [ACE-Step 1.5](https://github.com/ACE-Step/ACE-Step-1.5) | **Local GPU** | Free, open source | Very good | Full songs with vocals from lyrics plus style tags. Runs on under 4 GB of VRAM, about 10 s per song on an RTX 3090. Supports 50+ lyric languages. Ships a REST server we call. |
| `elevenlabs`: [ElevenLabs Music](https://elevenlabs.io/music) | Cloud | Paid per generation | Excellent | Section-by-section composition plan. Licensed for commercial use. |
| `none` | – | – | – | Lyrics only. Useful for testing prompts. |

Suno and Udio produce great results but have **no official public API**, so they aren't
included. Other open models to look at later: YuE and DiffRhythm.

**Lyrics** come from Claude through the Anthropic API (cloud). Claude reads your resume
(PDF natively, or DOCX/TXT/MD) and returns a structured song plan: title, style tags
such as `rap, boom bap, female vocals`, BPM, key, and `[verse]` / `[chorus]` sections.
The singer gender you pick is always added as the vocal tag.

## Setup

```bash
git clone <this repo> && cd resongme
python -m venv .venv && source .venv/bin/activate
pip install -e ".[ui]"            # add ,elevenlabs for the cloud backend
cp .env.example .env              # put your ANTHROPIC_API_KEY in it
```

### Run the local music server (ACE-Step 1.5)

You need an NVIDIA GPU (CUDA), Apple Silicon or AMD ROCm. In a separate terminal:

```bash
git clone https://github.com/ACE-Step/ACE-Step-1.5 && cd ACE-Step-1.5
uv sync
uv run acestep-api                # serves http://localhost:8001, downloads models on first run
```

If it runs on another machine, set `ACESTEP_URL` in `.env`. That works well with a
cloud GPU box.

## Usage

### CLI

```bash
resongme examples/sample_resume.md --genre rap --voice male --mood "hype, confident"
resongme ~/cv.pdf -g pop -v female -d 180 -x "focus on my move from teaching to tech"
resongme ~/cv.pdf -g country -v duet -b elevenlabs
resongme ~/cv.pdf -g k-pop -v female -b none          # lyrics only
```

The song (`output/<title>.mp3`) and its lyrics (`output/<title>.md`) are written to `output/`.

| Flag | Default | Meaning |
|---|---|---|
| `-g/--genre` | `pop` | Any genre: rap, pop, rock, country, r&b, edm, jazz, metal, lo-fi... |
| `-v/--voice` | `female` | `male`, `female`, `duet`, `choir`, `any` |
| `-m/--mood` | – | e.g. "triumphant", "funny", "chill" |
| `-d/--duration` | `150` | Seconds (10–600) |
| `-l/--language` | `en` | Lyrics language |
| `-x/--extra` | – | Free-form direction for the songwriter |
| `-b/--backend` | `acestep` | `acestep`, `elevenlabs`, `none` |
| `-f/--format` | `mp3` | `mp3`, `wav`, `flac` |

### Web UI

```bash
python -m resongme.ui             # opens a Gradio page: upload the resume, pick options, play the song
```

### From Python

```python
from resongme.pipeline import make_song
from resongme.song import SongRequest

result = make_song("cv.pdf", SongRequest(genre="rap", voice="female"), backend="acestep")
print(result.plan.lyrics(), result.audio_path)
```

## Project layout

```
resongme/
  resume.py           load PDF/DOCX/TXT/MD into Claude content blocks
  lyricist.py         Claude call → structured SongPlan (JSON schema output)
  song.py             SongRequest / SongPlan types, lyric + caption formatting
  pipeline.py         resume → lyrics → audio, writes files to output/
  backends/
    acestep.py        local ACE-Step 1.5 REST client (release_task → query_result → /v1/audio)
    elevenlabs.py     ElevenLabs Music composition-plan client
  cli.py, ui.py       command line and Gradio front ends
tests/                unit tests (no network needed): pytest
```

## Adding another music backend

Implement `render(plan: SongPlan, out_path: Path) -> Path` (see `backends/base.py`) and
register it in `backends/__init__.py`. `plan.caption()` gives the style prompt and
`plan.lyrics()` gives the tagged lyrics.

## Privacy

Your resume goes to the Anthropic API to write the lyrics. With the `acestep` backend,
only the lyrics and style tags go to your own music server. The songwriter prompt keeps
emails, phone numbers and addresses out of the lyrics.
