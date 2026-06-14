"""Calibrate the twin's baseline running against a static historical NTES dump.

The acquisition of fine-grained historical data is itself unsolved (audit-02 §3.8); we use
whatever dump is available, state its limits, and fit running times / dwell distributions so
the twin's *normal* day matches reality before scenarios are injected.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean


def calibrate(network: "object", timetable: "object", dump_path: str) -> dict:
    """Fit baseline parameters to a static historical dump.

    The dump is a CSV (``train_no,station,delay_min``) or a JSON list of the same records —
    a static NTES-style export. We compute the observed per-station delay bias so the twin's
    "normal" day can be nudged toward reality before scenarios are injected.

    Acquiring fine-grained historical data is itself unsolved (audit-02 §3.8); with no dump we
    return documented defaults. ``timetable`` is accepted for a future running-time fit (the
    delay-only dump can't drive it yet).

    Returns a parameter dict consumed by ``SimulationEngine``.
    """
    path = Path(dump_path)
    if not path.exists():
        return {"calibrated": False, "n_records": 0,
                "running_time_factor": 1.0, "station_delay_bias_min": {}}

    known = {s.code for s in network.stations()}
    by_station: dict[str, list[float]] = {}
    for r in _read(path):
        station = r["station"]
        if station in known:  # ignore stations outside this section
            by_station.setdefault(station, []).append(float(r["delay_min"]))

    bias = {st: round(mean(v), 2) for st, v in by_station.items()}
    n = sum(len(v) for v in by_station.values())
    return {"calibrated": True, "n_records": n,
            "running_time_factor": 1.0, "station_delay_bias_min": bias}


def _read(path: Path) -> list[dict]:
    if path.suffix == ".json":
        return json.loads(path.read_text())
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))
