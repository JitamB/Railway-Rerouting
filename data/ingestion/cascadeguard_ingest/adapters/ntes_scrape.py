"""Optional enrichment adapter — NTES HTML scrape behind a circuit-breaker.

There is **no official public NTES API** (audit-01 §3); scraping the enquiry portal is
brittle, rate-limited, and ToS-grey. Disabled by default (``CG_NTES_SCRAPE_ENABLED=false``)
and always wrapped by ``circuit_breaker`` so it can never take the system down on stage.
"""

from __future__ import annotations

from typing import Callable, Iterator

from ..circuit_breaker import CircuitBreaker


class NtesScrapeAdapter:
    """Best-effort scrape; optional, never the spine."""

    def __init__(
        self,
        enabled: bool = False,
        breaker: CircuitBreaker | None = None,
        scrape_fn: Callable[[], list[dict]] | None = None,
    ) -> None:
        self.enabled = enabled
        self.breaker = breaker or CircuitBreaker()
        self._scrape_fn = scrape_fn or self._no_scraper

    def stream(self) -> Iterator[dict]:
        """Yield enrichment events when enabled and the breaker is closed."""
        if not self.enabled:
            return  # off by default — never the spine
        try:
            events = self.breaker.call(self._scrape_fn)
        except Exception:
            return  # breaker open or scrape failed: degrade silently, twin/COA carry on
        yield from events

    @staticmethod
    def _no_scraper() -> list[dict]:
        raise RuntimeError("no NTES scraper configured (ToS-grey; off by default)")
