"""Weather as a REGIME variable + caution-order / TSR signals.

Weather's real effect on rail is discrete operating-regime shifts (fog -> 60 km/h + caution
orders; monsoon -> patrolling/TSRs; heat -> buckling speed cuts), not a smooth "severity
score" (audit-04 §4). This adapter emits a regime label that switches the model's operating
point, and ingests actual caution-order/TSR signals where obtainable.
"""

from __future__ import annotations


class WeatherTsrAdapter:
    def __init__(self, api_key: str | None = None) -> None:
        ...

    def regime(self, route: list[str]) -> str:
        """Return a regime label: 'normal' | 'fog' | 'monsoon' | 'heat'."""
        ...
