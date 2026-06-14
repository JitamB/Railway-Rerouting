"""Circuit-breaker wrapping the optional NTES scrape.

Trips on repeated rate-limits/errors so a flaky scrape can never take the system down — the
twin/COA path stays the spine (audit-01 §3, audit-04 bonus: ToS/IP-ban risk).

CLOSED: calls pass through. After ``fail_threshold`` consecutive failures it goes OPEN and
short-circuits (no call) for ``reset_after_s``, then HALF_OPEN to probe: one success closes it,
one failure re-opens it.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Callable


class BreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(RuntimeError):
    """Raised by ``call()`` when the breaker is OPEN and the call is short-circuited."""


class CircuitBreaker:
    def __init__(
        self,
        fail_threshold: int = 5,
        reset_after_s: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.fail_threshold = fail_threshold
        self.reset_after_s = reset_after_s
        self._clock = clock
        self._failures = 0
        self._opened_at: float | None = None
        self._state = BreakerState.CLOSED

    @property
    def state(self) -> BreakerState:
        if self._state is BreakerState.OPEN and self._clock() - self._opened_at >= self.reset_after_s:
            self._state = BreakerState.HALF_OPEN
        return self._state

    def call(self, fn, *args, **kwargs):
        """Invoke ``fn`` unless OPEN; record success/failure and update state."""
        if self.state is BreakerState.OPEN:
            raise CircuitOpenError("circuit is open; call short-circuited")
        try:
            result = fn(*args, **kwargs)
        except Exception:
            self._on_failure()
            raise
        self._on_success()
        return result

    def _on_success(self) -> None:
        self._failures = 0
        self._opened_at = None
        self._state = BreakerState.CLOSED

    def _on_failure(self) -> None:
        self._failures += 1
        if self._state is BreakerState.HALF_OPEN or self._failures >= self.fail_threshold:
            self._state = BreakerState.OPEN
            self._opened_at = self._clock()
