"""Discrete-event simulation engine for the CascadeGuard digital twin.

Advances trains over block sections under SimPy, respecting headways and platform
occupancy, and emits train-position / delay events compatible with the ingestion
contract (see ``shared/schemas/events.schema.json``). Primary data source — runs
offline and deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import simpy

from .network import SectionNetwork
from .timetable import Timetable


@dataclass
class TrainEvent:
    """A single emitted position/delay event."""

    train_no: str
    station: str
    event_time: float  # simulation minutes (event-time, not wall-clock)
    delay_min: float


class SimulationEngine:
    """Discrete-event clock driving the twin.

    A train is a SimPy process moving stop-to-stop. Three forces create delay and let it
    cascade across otherwise-unrelated trains:
      * **block headway** — successive trains entering the same block keep a minimum gap;
      * **platform capacity** — arrivals queue for a platform at each station;
      * **rake links** — an outbound service cannot depart until its inbound rake has
        arrived and turned around, so an inbound delay propagates to a different train.

    Disruptions (``scenarios.py``) set the hooks below before ``run()``:
      * ``station_closed[code] = (start, end)`` — a train arriving inside this window is held
        until ``end`` (an OHE/section failure); trains arriving before or after pass freely;
      * ``running_time_factor`` — multiplies every block run time (e.g. a fog regime).
    On a clean run every train follows the timetable exactly, so baseline delay is ~0.
    """

    def __init__(
        self,
        network: SectionNetwork,
        timetable: Timetable,
        seed: int = 0,
        config_path: str | None = None,
    ) -> None:
        self.network = network
        self.timetable = timetable
        self.seed = seed
        self.config_path = config_path  # lets inject() locate scenario definitions
        # disruption hooks — mutated by scenarios.apply() before run().
        self.station_closed: dict[str, tuple[float, float]] = {}
        self.running_time_factor: float = 1.0
        self.regime: str = "normal"
        self._events: list[TrainEvent] = []

    def run(self, horizon_min: float) -> Iterator[TrainEvent]:
        """Run the twin and yield events in event-time order."""
        env = simpy.Environment()
        net, tt = self.network, self.timetable

        platforms = {s.code: simpy.Resource(env, capacity=s.platforms) for s in net.stations()}
        # Per-directed-block headway: last entry sim-time, enforced as a minimum gap.
        block = {}
        for b in net.block_sections():
            block[(b.from_station, b.to_station)] = {"headway": b.headway_min, "last": -1e9}
            block[(b.to_station, b.from_station)] = {"headway": b.headway_min, "last": -1e9}

        rake_inbound = {lk.inbound: lk for lk in tt.rake_links()}
        rake_outbound = {lk.outbound: lk for lk in tt.rake_links()}
        rake_ready = {lk.outbound: env.event() for lk in tt.rake_links()}

        self._events = []

        def fire_rake_ready(link):
            # Called when the inbound rake reaches its terminus; outbound can leave after turnaround.
            yield env.timeout(link.min_turnaround_min)
            rake_ready[link.outbound].succeed(env.now)

        def service_proc(svc):
            stops = svc.stops
            origin = stops[0]

            if svc.train_no in rake_outbound:
                ready_at = yield rake_ready[svc.train_no]
                depart = max(svc.sched_dep_min[origin], ready_at)
            else:
                depart = svc.sched_dep_min[origin]
            if env.now < depart:
                yield env.timeout(depart - env.now)

            for frm, to in zip(stops, stops[1:]):
                bh = block[(frm, to)]
                if env.now < bh["last"] + bh["headway"]:
                    yield env.timeout(bh["last"] + bh["headway"] - env.now)
                bh["last"] = env.now

                run_time = svc.sched_arr_min[to] - svc.sched_dep_min[frm]
                yield env.timeout(run_time * self.running_time_factor)

                win = self.station_closed.get(to)
                if win is not None and win[0] <= env.now < win[1]:
                    yield env.timeout(win[1] - env.now)

                req = platforms[to].request()
                yield req
                arr = env.now
                self._events.append(
                    TrainEvent(svc.train_no, to, arr, arr - svc.sched_arr_min[to])
                )
                if to == stops[-1] and svc.train_no in rake_inbound:
                    env.process(fire_rake_ready(rake_inbound[svc.train_no]))
                if to != stops[-1]:
                    yield env.timeout(svc.sched_dep_min[to] - svc.sched_arr_min[to])
                platforms[to].release(req)

        for svc in tt.services():
            env.process(service_proc(svc))
        env.run(until=horizon_min)

        for ev in sorted(self._events, key=lambda e: (e.event_time, e.train_no)):
            yield ev

    def inject(self, scenario_id: str) -> None:
        """Arm a disruption scenario before ``run()`` (see ``scenarios.py``).

        Looks the scenario up by id in ``config_path`` and applies it to this engine.
        Scenarios set the hooks above; they take effect on the next ``run()``.
        """
        if self.config_path is None:
            raise ValueError("inject() needs config_path; pass it to SimulationEngine(...) "
                             "or call scenarios.apply(engine, scenario) directly.")
        from . import scenarios  # local import avoids a module-load cycle

        for sc in scenarios.load_scenarios(self.config_path):
            if sc.id == scenario_id:
                scenarios.apply(self, sc)
                return
        raise KeyError(f"unknown scenario {scenario_id!r} in {self.config_path}")
