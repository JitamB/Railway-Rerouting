"""Discrete-event simulation engine for the CascadeGuard digital twin.

Advances trains over block sections under SimPy, respecting headways and platform
occupancy, and emits train-position / delay events compatible with the ingestion
contract (see ``shared/schemas/events.schema.json``). Primary data source — runs
offline and deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass
class TrainEvent:
    """A single emitted position/delay event."""

    train_no: str
    station: str
    event_time: float  # simulation seconds (event-time, not wall-clock)
    delay_min: float


class SimulationEngine:
    """Discrete-event clock driving the twin."""

    def __init__(self, network: "object", timetable: "object", seed: int = 0) -> None:
        ...

    def run(self, horizon_min: float) -> Iterator[TrainEvent]:
        """Run the twin and yield events in event-time order."""
        ...

    def inject(self, scenario_id: str) -> None:
        """Apply a disruption scenario mid-run (see ``scenarios.py``)."""
        ...
