"""Validation / anomaly gate between ingestion and the models.

Garbage upstream (stale timestamps, zeroed positions, duplicates, impossible jumps) injects
phantom cascades if it reaches the graph (audit-04 §8). This gate validates and quarantines —
it never crashes on a bad record.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GateResult:
    ok: bool
    reason: str | None = None


class AnomalyGate:
    def __init__(self, vmax_kmph: float = 160.0) -> None:
        ...

    def check(self, event: dict, prev: dict | None) -> GateResult:
        """Schema + de-dup + monotonic event-time + physical-plausibility check."""
        ...

    def quarantine(self, event: dict, reason: str) -> None:
        """Route a suspect event to the dead-letter queue."""
        ...
