"""Section topology for the digital twin: stations, block sections, platforms, headways.

Loaded from a YAML section definition (see ``config/section.example.yaml``). This is the
physical substrate the engine moves trains over and the basis for the dependency graph.
"""

from __future__ import annotations

from dataclasses import dataclass


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

    @classmethod
    def from_yaml(cls, path: str) -> "SectionNetwork":
        ...

    def stations(self) -> list[Station]:
        ...

    def block_sections(self) -> list[BlockSection]:
        ...
