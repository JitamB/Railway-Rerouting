"""Circuit-breaker wrapping the optional NTES scrape.

Trips on repeated rate-limits/errors so a flaky scrape can never take the system down — the
twin/COA path stays the spine (audit-01 §3, audit-04 bonus: ToS/IP-ban risk).
"""

from __future__ import annotations

from enum import Enum


class BreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, fail_threshold: int = 5, reset_after_s: float = 60.0) -> None:
        ...

    @property
    def state(self) -> BreakerState:
        ...

    def call(self, fn, *args, **kwargs):
        """Invoke ``fn`` unless OPEN; record success/failure and update state."""
        ...
