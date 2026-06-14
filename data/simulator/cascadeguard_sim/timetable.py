"""Scheduled services and the links that carry delay across otherwise-unrelated trains.

Critically includes **rake links** (the same physical trainset turning around as a later
service) and crew/loco turnarounds — top cascade sources that a station-adjacency view
misses (audit-02 §3.2).
"""

from __future__ import annotations

from dataclasses import dataclass

import yaml


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


@dataclass
class ServiceLink:
    """A crew or loco hand-off: one service's resource signs on to another."""

    from_service: str
    to_service: str


class Timetable:
    def __init__(
        self,
        services: list[Service],
        rake_links: list[RakeLink],
        crew_links: list[ServiceLink] | None = None,
        loco_links: list[ServiceLink] | None = None,
    ) -> None:
        self._services = services
        self._rake_links = rake_links
        self._crew_links = crew_links or []
        self._loco_links = loco_links or []
        self._by_train = {s.train_no: s for s in services}

    @classmethod
    def from_yaml(cls, path: str) -> "Timetable":
        with open(path) as fh:
            cfg = yaml.safe_load(fh)

        services = []
        for s in cfg.get("services", []):
            stops = [stop["station"] for stop in s["stops"]]
            arr = {stop["station"]: float(stop["arr"]) for stop in s["stops"] if "arr" in stop}
            dep = {stop["station"]: float(stop["dep"]) for stop in s["stops"] if "dep" in stop}
            services.append(Service(train_no=s["train_no"], stops=stops,
                                    sched_arr_min=arr, sched_dep_min=dep))

        rake_links = [
            RakeLink(
                rake_id=r["rake_id"],
                inbound=r["inbound"],
                outbound=r["outbound"],
                min_turnaround_min=float(r["min_turnaround_min"]),
            )
            for r in cfg.get("rakes", [])
        ]
        crew_links = [ServiceLink(l["from"], l["to"]) for l in cfg.get("crew_links", [])]
        loco_links = [ServiceLink(l["from"], l["to"]) for l in cfg.get("loco_links", [])]
        return cls(services, rake_links, crew_links, loco_links)

    def services(self) -> list[Service]:
        return self._services

    def rake_links(self) -> list[RakeLink]:
        return self._rake_links

    def crew_links(self) -> list[ServiceLink]:
        return self._crew_links

    def loco_links(self) -> list[ServiceLink]:
        return self._loco_links

    def service(self, train_no: str) -> Service:
        return self._by_train[train_no]
