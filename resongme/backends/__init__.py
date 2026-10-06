from .base import AudioBackend


def get_backend(name: str) -> AudioBackend:
    name = name.lower()
    if name == "acestep":
        from .acestep import AceStepBackend

        return AceStepBackend()
    if name == "elevenlabs":
        from .elevenlabs import ElevenLabsBackend

        return ElevenLabsBackend()
    if name == "none":
        from .base import LyricsOnlyBackend

        return LyricsOnlyBackend()
    raise ValueError(f"Unknown backend {name!r}; choose acestep, elevenlabs or none")


BACKENDS = ("acestep", "elevenlabs", "none")

__all__ = ["AudioBackend", "BACKENDS", "get_backend"]
