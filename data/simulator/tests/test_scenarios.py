from pathlib import Path

from cascadeguard_sim.engine import SimulationEngine
from cascadeguard_sim.network import SectionNetwork
from cascadeguard_sim.scenarios import load_scenarios
from cascadeguard_sim.timetable import Timetable

CONFIG = str(Path(__file__).resolve().parents[1] / "config" / "section.example.yaml")
HORIZON = 160


def _engine() -> SimulationEngine:
    return SimulationEngine(
        SectionNetwork.from_yaml(CONFIG), Timetable.from_yaml(CONFIG), config_path=CONFIG
    )


def _delays(events):
    return {(e.train_no, e.station): e.delay_min for e in events}


def test_load_scenarios():
    scs = {s.id: s for s in load_scenarios(CONFIG)}
    assert {"fog_regime", "ohe_failure"} <= set(scs)
    assert scs["ohe_failure"].kind == "infra"
    assert scs["ohe_failure"].params["location"] == "MGS"


def test_ohe_failure_blooms_downstream():
    baseline = _delays(_engine().run(horizon_min=HORIZON))
    assert max(baseline.values()) == 0  # clean day

    eng = _engine()
    eng.inject("ohe_failure")
    injected = _delays(eng.run(horizon_min=HORIZON))

    # The held train at the failure station (MGS) is late...
    assert injected[("12301", "MGS")] > 0
    # ...and that delay propagates DOWNSTREAM to the next station (BSB).
    assert injected[("12301", "BSB")] > 0
    # ...and ACROSS trains via the rake link: 12301 -> 12302 turnaround.
    assert injected[("12302", "MGS")] > 0
    assert injected[("12302", "PNBE")] > 0

    # The bloom is bounded: a train that reaches MGS after the window escapes clean.
    assert injected[("15049", "MGS")] == 0

    # Net effect: strictly more total delay than baseline.
    assert sum(injected.values()) > sum(baseline.values())


def test_fog_regime_slows_every_train():
    eng = _engine()
    eng.inject("fog_regime")
    assert eng.regime == "fog"
    assert eng.running_time_factor > 1.0
    injected = _delays(eng.run(horizon_min=HORIZON))
    # A blanket slowdown makes arrivals late across the board.
    assert sum(injected.values()) > 0
