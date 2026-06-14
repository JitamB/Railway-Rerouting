"""Map-matching + smoothing to defeat GPS drift -> phantom cascades (audit-04 §3).

Snaps a raw GPS/IRNSS fix to the nearest node on the track corridor, then blends it with the
prediction from the previous fix weighted by how well it snapped (a confidence-weighted 1-D
filter). A fix far off the corridor gets low confidence and is pulled toward the prediction
instead of trusted, so a teleport can't yank the position. Where available, track-circuit /
axle-counter occupancy would fuse in as ground truth (mocked here).

``track_graph`` is the corridor as an ordered list of ``(station_code, lat, lon)``; the GPS
coordinates are mocked honestly until a real RTIS feed exists.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class MatchedFix:
    block_id: str
    position_km: float
    speed_kmph: float
    confidence: float


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


class MapMatcher:
    NOMINAL_DT_S = 30.0  # assumed RTIS update cadence, used to turn Δposition into a speed
    SNAP_SCALE_KM = 2.0  # confidence decay: a fix this far off-track has confidence ~1/e

    def __init__(self, track_graph: list[tuple[str, float, float]]) -> None:
        self.nodes = list(track_graph)
        self.km = [0.0]
        for i in range(1, len(self.nodes)):
            self.km.append(self.km[-1] + _haversine_km(self.nodes[i - 1][1:], self.nodes[i][1:]))

    def match(self, lat: float, lon: float, prev: MatchedFix | None) -> MatchedFix:
        """Snap to track + smooth; low confidence down-weights the fix."""
        residuals = [_haversine_km((lat, lon), (n[1], n[2])) for n in self.nodes]
        i = min(range(len(self.nodes)), key=residuals.__getitem__)
        confidence = math.exp(-residuals[i] / self.SNAP_SCALE_KM)
        measured_km = self.km[i]

        if prev is None:
            position_km, speed_kmph = measured_km, 0.0
        else:
            dt_h = self.NOMINAL_DT_S / 3600
            predicted = prev.position_km + prev.speed_kmph * dt_h
            # trust the measurement in proportion to its snap confidence (Kalman-flavored).
            position_km = confidence * measured_km + (1 - confidence) * predicted
            speed_kmph = abs(position_km - prev.position_km) / dt_h

        return MatchedFix(self.nodes[i][0], position_km, speed_kmph, confidence)
