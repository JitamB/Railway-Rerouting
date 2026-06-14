"""Validation / anomaly gate between ingestion and the models.

Garbage upstream (stale timestamps, zeroed positions, duplicates, impossible jumps) injects
phantom cascades if it reaches the graph (audit-04 §8). This gate validates and quarantines —
it never crashes on a bad record.

Checks, in order: schema → de-dup → monotonic event-time → physical plausibility
(``Δpos ≤ vmax·Δt``). The plausibility check runs only when station positions are known;
the digital twin (no GPS) passes on schema/order alone, while the GPS feeds get the full guard.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..contracts import event_errors


@dataclass
class GateResult:
    ok: bool
    reason: str | None = None


class AnomalyGate:
    def __init__(self, vmax_kmph: float = 160.0, station_km: dict[str, float] | None = None) -> None:
        self.vmax_kmph = vmax_kmph
        self.station_km = station_km or {}  # cumulative km per station, for the speed check
        self.dead_letter: list[tuple[dict, str]] = []

    def check(self, event: dict, prev: dict | None) -> GateResult:
        """Schema + de-dup + monotonic event-time + physical-plausibility check."""
        errors = event_errors(event)
        if errors:
            return GateResult(False, f"schema: {errors[0]}")

        if prev is not None:
            same_train = event["train_no"] == prev["train_no"]

            if same_train and self._key(event) == self._key(prev):
                return GateResult(False, "duplicate")

            if same_train:
                et, pt = self._t(event), self._t(prev)
                if et < pt:
                    return GateResult(False, "non-monotonic event-time")

                km = self.station_km
                if event["station"] in km and prev["station"] in km:
                    dkm = abs(km[event["station"]] - km[prev["station"]])
                    dt_h = (et - pt).total_seconds() / 3600
                    if dkm > 0 and dt_h <= 0:
                        return GateResult(False, "displacement with zero elapsed time")
                    if dt_h > 0 and dkm / dt_h > self.vmax_kmph:
                        speed = dkm / dt_h
                        return GateResult(
                            False, f"implausible speed {speed:.0f} km/h > vmax {self.vmax_kmph:.0f}"
                        )

        return GateResult(True)

    def quarantine(self, event: dict, reason: str) -> None:
        """Route a suspect event to the dead-letter queue."""
        self.dead_letter.append((event, reason))

    @staticmethod
    def _key(event: dict) -> tuple:
        return (event["train_no"], event["station"], event["event_time"])

    @staticmethod
    def _t(event: dict) -> datetime:
        return datetime.fromisoformat(event["event_time"])
