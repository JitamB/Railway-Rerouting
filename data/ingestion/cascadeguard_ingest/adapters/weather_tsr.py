"""Weather as a REGIME variable + caution-order / TSR signals.

Weather's real effect on rail is discrete operating-regime shifts (fog -> 60 km/h + caution
orders; monsoon -> patrolling/TSRs; heat -> buckling speed cuts), not a smooth "severity
score" (audit-04 §4). This adapter emits a regime label that switches the model's operating
point, and ingests actual caution-order/TSR signals where obtainable.

Mocked honestly: with no OpenWeather key we return a configurable regime (default ``normal``);
the real path would classify a live forecast/TSR feed into the same labels.
"""

from __future__ import annotations

REGIMES = ("normal", "fog", "monsoon", "heat")


class WeatherTsrAdapter:
    def __init__(self, api_key: str | None = None, default_regime: str = "normal") -> None:
        self.api_key = api_key
        self.default_regime = default_regime
        self._overrides: dict[str, str] = {}  # station -> regime (demo/test injection)

    def set_regime(self, station: str, regime: str) -> None:
        if regime not in REGIMES:
            raise ValueError(f"regime must be one of {REGIMES}, got {regime!r}")
        self._overrides[station] = regime

    def regime(self, route: list[str]) -> str:
        """Return a regime label: 'normal' | 'fog' | 'monsoon' | 'heat'."""
        # Mock: any station on the route under a non-normal regime governs the route.
        for station in route:
            if station in self._overrides:
                return self._overrides[station]
        return self.default_regime
