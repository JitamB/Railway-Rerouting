"""Text-to-speech for spoken replies in the passenger's language (optional).

Makes the helpline bidirectional for low-literacy / hands-free use. Bhashini TTS default;
falls back to text-only when unavailable.
"""

from __future__ import annotations


class TTS:
    def __init__(self, provider: str = "bhashini") -> None:
        ...

    def synthesize(self, text: str, language: str) -> bytes:
        """Return audio bytes for ``text`` in ``language`` (empty/None if TTS unavailable)."""
        ...
