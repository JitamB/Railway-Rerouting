"""Disruption injectors for the twin.

Generates the rare, structurally-different events that matter most and have no historical
analog — derailments, OHE failures, fog regimes, freight conflicts — so the model can be
trained/validated on the *shape* of a real cascade (audit-04 §2/§6).
"""

from __future__ import annotations

from dataclasses import dataclass

import yaml

# Assumed clear-weather line speed, used only to translate a regime speed cap
# (e.g. fog → 60 km/h) into a block run-time multiplier. A modeling choice, not a measurement.
CLEAR_SPEED_KMPH = 80.0


@dataclass
class Scenario:
    id: str
    kind: str  # "weather" | "infra" | "freight" | "accident"
    params: dict


def load_scenarios(path: str) -> list[Scenario]:
    """Read scenario definitions from a section config file."""
    with open(path) as fh:
        cfg = yaml.safe_load(fh)
    out = []
    for sc in cfg.get("scenarios", []):
        params = {k: v for k, v in sc.items() if k not in ("id", "type")}
        out.append(Scenario(id=sc["id"], kind=sc["type"], params=params))
    return out


def apply(engine: "object", scenario: Scenario) -> None:
    """Arm a disruption on the engine by setting its hooks (takes effect on next run())."""
    p = scenario.params
    if scenario.kind == "infra":
        # OHE / section failure: close a station for [start, start+duration).
        start = float(p["start_min"])
        engine.station_closed[p["location"]] = (start, start + float(p["duration_min"]))
    elif scenario.kind == "weather":
        # Fog/monsoon regime: cap speed → every block runs slower.
        engine.regime = p.get("regime", "fog")
        engine.running_time_factor = CLEAR_SPEED_KMPH / float(p["speed_kmph"])
    else:
        raise ValueError(f"unsupported scenario kind {scenario.kind!r} (id={scenario.id})")
