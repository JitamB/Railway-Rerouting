"""Speech-to-text for regional Indian languages.

Bhashini / ULCA is the India-credible default (govt ASR/NMT/TTS stack); Whisper is the offline
fallback. Not openly turnkey for every language pair, so adapters are mocked honestly behind a
clean interface. Optionally machine-translates the transcript to a working language for the
agent, then replies are translated back.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Transcript:
    text: str
    language: str          # detected/declared source language (e.g. "hi", "bn", "ta")
    confidence: float


class ASR:
    def __init__(self, provider: str = "bhashini") -> None:  # "bhashini" | "whisper"
        ...

    def transcribe(self, audio: bytes, language: str | None = None) -> Transcript:
        """Return a transcript; ``language`` may be provided or auto-detected."""
        ...

    def translate(self, text: str, src: str, tgt: str) -> str:
        """NMT between Indian languages and the agent's working language."""
        ...
