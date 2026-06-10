"""Scheduled services and the links that carry delay across otherwise-unrelated trains.

Critically includes **rake links** (the same physical trainset turning around as a later
service) and crew/loco turnarounds — top cascade sources that a station-adjacency view
misses (audit-02 §3.2).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Service:
    train_no: str
    stops: list[str]
    sched_arr_min: dict[str, float]
    sched_dep_min: dict[str, float]


@dataclass
class RakeLink:
    """Inbound service -> outbound service on the same physical rake."""

    rake_id: str
    inbound: str
    outbound: str
    min_turnaround_min: float


class Timetable:
    @classmethod
    def from_yaml(cls, path: str) -> "Timetable":
        ...

    def services(self) -> list[Service]:
        ...

    def rake_links(self) -> list[RakeLink]:
        ...
