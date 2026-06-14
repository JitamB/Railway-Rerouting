"""Primary adapter — reads events from the digital twin (data/simulator).

Deterministic and always-available; this is the spine on stage and in dev. It is also the one
place the simulation domain (sim-minutes) is mapped onto the wire contract: ISO event-time +
received-time (data-age) + source, per shared/schemas/events.schema.json.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterator

from cascadeguard_sim.engine import SimulationEngine
from cascadeguard_sim.network import SectionNetwork
from cascadeguard_sim.timetable import Timetable

# Fixed demo epoch so sim-minute 0 maps to a stable wall-clock event-time (deterministic).
DEFAULT_EPOCH = datetime(2026, 6, 12, 6, 0, tzinfo=timezone.utc)


class TwinAdapter:
    """Streams ``TrainEvent``-shaped dicts from a running simulation."""

    def __init__(
        self,
        section_config: str,
        *,
        horizon_min: float = 160,
        scenario: str | None = None,
        start_time: datetime | None = None,
        source: str = "twin",
        received_lag_s: float = 30.0,
    ) -> None:
        self.horizon_min = horizon_min
        self.source = source
        self.start_time = start_time or DEFAULT_EPOCH
        self.received_lag_s = received_lag_s
        self._engine = SimulationEngine(
            SectionNetwork.from_yaml(section_config),
            Timetable.from_yaml(section_config),
            config_path=section_config,
        )
        if scenario:
            self._engine.inject(scenario)

    def stream(self) -> Iterator[dict]:
        """Yield normalized events conforming to shared/schemas/events.schema.json."""
        for ev in self._engine.run(horizon_min=self.horizon_min):
            event_dt = self.start_time + timedelta(minutes=ev.event_time)
            received_dt = event_dt + timedelta(seconds=self.received_lag_s)
            yield {
                "train_no": ev.train_no,
                "station": ev.station,
                "event_time": event_dt.isoformat(),
                "received_time": received_dt.isoformat(),
                "delay_min": ev.delay_min,
                "source": self.source,
                "regime": self._engine.regime,
                "position_confidence": 1.0,  # the twin is ground truth
            }
