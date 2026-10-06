from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from .backends import BACKENDS
from .song import GENRES, VOICES, SongRequest


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    p = argparse.ArgumentParser(prog="resongme", description="Turn your resume into a song.")
    p.add_argument("resume", help="Path to your resume (.pdf, .docx, .txt, .md)")
    p.add_argument("-g", "--genre", default="pop", help=f"e.g. {', '.join(GENRES)} (anything goes)")
    p.add_argument("-v", "--voice", default="female", choices=VOICES, help="Singer's voice")
    p.add_argument("-m", "--mood", default="", help='e.g. "triumphant", "chill", "funny"')
    p.add_argument("-d", "--duration", type=int, default=150, help="Song length in seconds (10-600)")
    p.add_argument("-l", "--language", default="en", help="Lyrics language code (en, es, hi, ...)")
    p.add_argument("-x", "--extra", default="", help="Any extra direction for the songwriter")
    p.add_argument("-b", "--backend", default="acestep", choices=BACKENDS,
                   help="acestep = local (free, GPU), elevenlabs = cloud, none = lyrics only")
    p.add_argument("-f", "--format", default="mp3", choices=("mp3", "wav", "flac"))
    p.add_argument("-o", "--out-dir", default="output")
    args = p.parse_args(argv)

    if not 10 <= args.duration <= 600:
        p.error("--duration must be between 10 and 600 seconds")

    from .pipeline import make_song  # imported late so --help works without deps configured

    request = SongRequest(
        genre=args.genre, voice=args.voice, mood=args.mood,
        duration_s=args.duration, language=args.language, extra=args.extra,
    )
    print(f"Writing a {args.genre} song ({args.voice} vocals) from {args.resume} ...", file=sys.stderr)
    try:
        result = make_song(args.resume, request, backend=args.backend,
                           out_dir=args.out_dir, audio_format=args.format)
    except Exception as e:  # surface a clean message on the CLI
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(result.plan.to_markdown())
    print(f"Lyrics: {result.lyrics_path}", file=sys.stderr)
    if result.audio_path:
        print(f"Audio:  {result.audio_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
