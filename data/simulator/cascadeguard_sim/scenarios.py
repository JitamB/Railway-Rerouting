"""Disruption injectors for the twin.

Generates the rare, structurally-different events that matter most and have no historical
analog — derailments, OHE failures, fog regimes, freight conflicts — so the model can be
trained/validated on the *shape* of a real cascade (audit-04 §2/§6).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Scenario:
    id: str
    kind: str  # "weather" | "infra" | "freight" | "accident"
    params: dict


def load_scenarios(path: str) -> list[Scenario]:
    """Read scenario definitions from a section config file."""
    ...


def apply(engine: "object", scenario: Scenario) -> None:
    """Mutate the running simulation to enact a disruption."""
    ...
