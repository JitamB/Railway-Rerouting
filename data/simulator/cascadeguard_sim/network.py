"""Section topology for the digital twin: stations, block sections, platforms, headways.

Loaded from a YAML section definition (see ``config/section.example.yaml``). This is the
physical substrate the engine moves trains over and the basis for the dependency graph.
"""

from __future__ import annotations

from dataclasses import dataclass

import yaml


@dataclass
class Station:
    code: str
    name: str
    platforms: int


@dataclass
class BlockSection:
    from_station: str
    to_station: str
    length_km: float
    headway_min: float


class SectionNetwork:
    """In-memory section topology built from a section config file."""

    def __init__(self, stations: list[Station], block_sections: list[BlockSection]) -> None:
        self._stations = stations
        self._blocks = block_sections
        self._by_code = {s.code: s for s in stations}

    @classmethod
    def from_yaml(cls, path: str) -> "SectionNetwork":
        with open(path) as fh:
            cfg = yaml.safe_load(fh)

        stations = [
            Station(code=s["code"], name=s["name"], platforms=int(s["platforms"]))
            for s in cfg.get("stations", [])
        ]
        blocks = [
            BlockSection(
                from_station=b["from"],
                to_station=b["to"],
                length_km=float(b["length_km"]),
                headway_min=float(b["headway_min"]),
            )
            for b in cfg.get("block_sections", [])
        ]
        return cls(stations, blocks)

    def stations(self) -> list[Station]:
        return self._stations

    def block_sections(self) -> list[BlockSection]:
        return self._blocks

    def station(self, code: str) -> Station:
        return self._by_code[code]
