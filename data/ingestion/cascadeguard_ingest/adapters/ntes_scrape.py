"""Optional enrichment adapter — NTES HTML scrape behind a circuit-breaker.

There is **no official public NTES API** (audit-01 §3); scraping the enquiry portal is
brittle, rate-limited, and ToS-grey. Disabled by default (``CG_NTES_SCRAPE_ENABLED=false``)
and always wrapped by ``circuit_breaker`` so it can never take the system down on stage.
"""

from __future__ import annotations

from typing import Iterator


class NtesScrapeAdapter:
    """Best-effort scrape; optional, never the spine."""

    def __init__(self, enabled: bool = False) -> None:
        ...

    def stream(self) -> Iterator[dict]:
        """Yield enrichment events when enabled and the breaker is closed."""
        ...
