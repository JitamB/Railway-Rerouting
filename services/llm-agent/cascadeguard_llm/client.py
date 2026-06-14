"""LLM client wrapper for alert phrasing — Groq (OpenAI-compatible, low-cost, fast).

Model id from ``GROQ_MODEL`` (default ``llama-3.1-8b-instant`` — a small, fast open model; the job
is a 2-3 sentence rephrase, not reasoning). Used only when a re-route crosses the notification
trigger, never on every inference cycle. The structured facts are AUTHORITATIVE; the model only
rephrases them — see ``phrasing.py`` (and it falls back to the template on any failure).

Swap providers by changing this one file: any OpenAI-compatible endpoint (Groq, OpenAI, Together,
a local Ollama/vLLM server) works with the same ``chat.completions`` call.
"""

from __future__ import annotations

import os

DEFAULT_MODEL = "llama-3.1-8b-instant"  # see https://console.groq.com/docs/models for current ids

SYSTEM_PROMPT = (
    "You rephrase Indian Railways re-route guidance for a passenger. The structured facts you "
    "are given are AUTHORITATIVE: copy every train number, platform, and time exactly as given "
    "— never invent, drop, or alter them. Reply with 2-3 calm, plain sentences. No preamble, "
    "no markdown, no lists."
)


class LlmClient:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.model = model or os.getenv("GROQ_MODEL", DEFAULT_MODEL)
        self._api_key = api_key or os.getenv("GROQ_API_KEY")
        self._client = None  # lazily created so the module imports without a key

    async def phrase(self, prompt: str, max_tokens: int = 200) -> str:
        """Return LLM-phrased prose (async; caller never blocks the alert on this).

        Raises if the LLM is unreachable / unconfigured — callers (``phrasing.enrich``) catch and
        fall back to the deterministic template, so delivery never depends on this.
        """
        if not self._api_key:
            raise RuntimeError("GROQ_API_KEY not set; fall back to the template")
        if self._client is None:
            from groq import AsyncGroq

            self._client = AsyncGroq(api_key=self._api_key)

        response = await self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return (response.choices[0].message.content or "").strip()
