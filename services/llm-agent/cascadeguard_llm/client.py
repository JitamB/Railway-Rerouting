"""Claude API client wrapper.

Model id from ``ANTHROPIC_MODEL`` (default ``claude-sonnet-4-6``). Used only when a re-route
crosses the notification trigger — not on every inference cycle.
"""

from __future__ import annotations

DEFAULT_MODEL = "claude-sonnet-4-6"


class ClaudeClient:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL) -> None:
        ...

    async def phrase(self, prompt: str, max_tokens: int = 200) -> str:
        """Return LLM-phrased prose (async; caller never blocks the alert on this)."""
        ...
