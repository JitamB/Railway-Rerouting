"""Text-to-speech for spoken replies in the passenger's language (optional).

Makes the helpline bidirectional for low-literacy / hands-free use. Bhashini TTS default;
falls back to text-only when unavailable.
"""

from __future__ import annotations


class TTS:
    """Honest TTS mock. Bhashini TTS isn't wired, so synthesis is unavailable by default and the
    helpline stays text-only (``synthesize`` returns ``b""``); ``enabled`` is the seam a real
    Bhashini/ULCA TTS client flips on without changing callers."""

    def __init__(self, provider: str = "bhashini", enabled: bool = False) -> None:
        self.provider = provider
        self.enabled = enabled

    def synthesize(self, text: str, language: str) -> bytes:
        """Return audio bytes for ``text`` in ``language`` (empty when TTS is unavailable)."""
        if not self.enabled:
            return b""
        raise NotImplementedError("wire a Bhashini/ULCA TTS client here")
