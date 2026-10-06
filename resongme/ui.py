"""Small web UI: `pip install -e .[ui]` then `python -m resongme.ui`."""

from __future__ import annotations

from dotenv import load_dotenv

from .backends import BACKENDS
from .pipeline import make_song
from .song import GENRES, VOICES, SongRequest


def generate(resume_file, genre, voice, mood, duration, language, extra, backend):
    if resume_file is None:
        raise ValueError("Upload your resume first.")
    path = resume_file if isinstance(resume_file, str) else resume_file.name
    request = SongRequest(genre=genre, voice=voice, mood=mood, duration_s=int(duration),
                          language=language, extra=extra)
    result = make_song(path, request, backend=backend)
    return result.plan.to_markdown(), str(result.audio_path) if result.audio_path else None


def build():
    import gradio as gr

    with gr.Blocks(title="ResongMe") as demo:
        gr.Markdown("# 🎤 ResongMe\nUpload your resume, pick a genre and a singer, get your song.")
        with gr.Row():
            with gr.Column():
                resume = gr.File(label="Resume", file_types=[".pdf", ".docx", ".txt", ".md"])
                genre = gr.Dropdown(list(GENRES), value="pop", label="Genre", allow_custom_value=True)
                voice = gr.Radio(list(VOICES), value="female", label="Singer")
                mood = gr.Textbox(label="Mood (optional)", placeholder="triumphant, funny, chill...")
                duration = gr.Slider(30, 300, value=150, step=10, label="Length (seconds)")
                language = gr.Textbox(value="en", label="Lyrics language")
                extra = gr.Textbox(label="Extra direction (optional)")
                backend = gr.Radio(list(BACKENDS), value="acestep", label="Audio backend")
                go = gr.Button("Make my song", variant="primary")
            with gr.Column():
                audio = gr.Audio(label="Your song", type="filepath")
                lyrics = gr.Markdown()
        go.click(generate, [resume, genre, voice, mood, duration, language, extra, backend], [lyrics, audio])
    return demo


if __name__ == "__main__":
    load_dotenv()
    build().launch()
