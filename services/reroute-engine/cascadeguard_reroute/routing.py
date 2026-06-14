"""Deterministic alternative-train query.

Given an origin/destination and current time, return the top-k candidate alternatives. This is
the deterministic part the LLM later phrases — the model predicts, the router enumerates, the
allocator chooses (clear separation of concerns). Candidates come from the twin timetable
(twin-first); in production the same query runs against the live timetable.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from cascadeguard_sim.timetable import Timetable

DEFAULT_SECTION_CONFIG = str(
    Path(__file__).resolve().parents[3] / "data" / "simulator" / "config" / "section.example.yaml"
)


@dataclass
class Candidate:
    train_no: str
    platform: str
    departs_min: float
    arrives_dest_min: float


@lru_cache(maxsize=4)
def _timetable(config: str) -> Timetable:
    return Timetable.from_yaml(config)


def _platform(train_no: str) -> str:
    # Platform assignment isn't in the timetable; mocked deterministically (the real value
    # comes from COA/RTIS in production, where it is safety-critical and never LLM-generated).
    return str(1 + int(train_no) % 6)


def find_alternatives(origin: str, dest: str, after_min: float, k: int = 3,
                      config: str = DEFAULT_SECTION_CONFIG) -> list[Candidate]:
    """Return up to ``k`` candidate trains from ``origin`` to ``dest`` after ``after_min``."""
    candidates = []
    for svc in _timetable(config).services():
        stops = svc.stops
        if origin not in stops or dest not in stops or stops.index(origin) >= stops.index(dest):
            continue
        departs = svc.sched_dep_min.get(origin)
        arrives = svc.sched_arr_min.get(dest)
        if departs is None or arrives is None or departs < after_min:
            continue
        candidates.append(Candidate(svc.train_no, _platform(svc.train_no), departs, arrives))

    candidates.sort(key=lambda c: c.arrives_dest_min)  # earliest arrival first
    return candidates[:k]
