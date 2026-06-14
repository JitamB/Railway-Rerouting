"""Speech-to-text for regional Indian languages.

Bhashini / ULCA is the India-credible default (govt ASR/NMT/TTS stack); Whisper is the offline
fallback. Not openly turnkey for every language pair, so adapters are mocked honestly behind a
clean interface. Optionally machine-translates the transcript to a working language for the
agent, then replies are translated back.
"""

from __future__ import annotations

from dataclasses import dataclass

# A clearly-labelled stand-in transcript, used when the audio carries no decodable text (real
# Bhashini/Whisper isn't wired). Mirrors the grievance contract sample so the demo stays coherent.
_MOCK_TRANSCRIPT = "B4 coach mein ek lawaris bag pada hai"


@dataclass
class Transcript:
    text: str
    language: str          # detected/declared source language (e.g. "hi", "bn", "ta")
    confidence: float


class ASR:
    """Honest ASR/NMT mock behind the real interface.

    No turnkey open API covers every Indian language pair, so this does not pretend to transcribe
    audio. Instead it decodes the clip as UTF-8 text when possible (so the app/tests can drive the
    pipeline with a real utterance) and otherwise returns a labelled stand-in transcript. Swap in
    a Bhashini/ULCA or Whisper client without touching callers.
    """

    def __init__(self, provider: str = "bhashini") -> None:  # "bhashini" | "whisper"
        self.provider = provider

    def transcribe(self, audio: bytes, language: str | None = None) -> Transcript:
        """Return a transcript; ``language`` may be provided or auto-detected."""
        try:
            text = audio.decode("utf-8").strip()
        except (UnicodeDecodeError, AttributeError):
            text = ""
        if not text:
            text = _MOCK_TRANSCRIPT
        return Transcript(text=text, language=language or "hi", confidence=0.95)

    def translate(self, text: str, src: str, tgt: str) -> str:
        """NMT between Indian languages and the agent's working language.

        Mocked as a passthrough — the intent classifier matches English *and* romanized-Hindi
        keywords directly, so routing works without a real translation engine. A real NMT adapter
        drops in here.
        """
        return text
