"""Map-matching + smoothing to defeat GPS drift -> phantom cascades (audit-04 §3).

Snaps raw GPS/IRNSS fixes to the nearest feasible block on the track graph and runs a
Kalman/particle filter to smooth position/speed and reject physically impossible jumps. Where
available, fuses against track-circuit / axle-counter occupancy (ground truth).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MatchedFix:
    block_id: str
    position_km: float
    speed_kmph: float
    confidence: float


class MapMatcher:
    def __init__(self, track_graph: "object") -> None:
        ...

    def match(self, lat: float, lon: float, prev: MatchedFix | None) -> MatchedFix:
        """Snap to track + Kalman-smooth; low confidence down-weights the fix."""
        ...
