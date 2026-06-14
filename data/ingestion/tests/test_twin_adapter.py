from pathlib import Path

from cascadeguard_ingest.adapters.twin_adapter import TwinAdapter
from cascadeguard_ingest.contracts import event_errors
from cascadeguard_sim.engine import SimulationEngine
from cascadeguard_sim.network import SectionNetwork
from cascadeguard_sim.timetable import Timetable

CONFIG = str(
    Path(__file__).resolve().parents[2] / "simulator" / "config" / "section.example.yaml"
)
HORIZON = 160


def _engine_events():
    eng = SimulationEngine(
        SectionNetwork.from_yaml(CONFIG), Timetable.from_yaml(CONFIG), config_path=CONFIG
    )
    return list(eng.run(horizon_min=HORIZON))


def test_adapter_matches_engine_and_is_contract_valid():
    engine_events = _engine_events()
    records = list(TwinAdapter(CONFIG, horizon_min=HORIZON).stream())

    # same events as the engine, in the same order
    assert len(records) == len(engine_events)
    for rec, ev in zip(records, engine_events):
        assert rec["train_no"] == ev.train_no
        assert rec["station"] == ev.station
        assert rec["delay_min"] == ev.delay_min
        assert rec["source"] == "twin"

    # every record validates against the frozen contract
    for rec in records:
        assert event_errors(rec) == [], rec

    # event-time ordering preserved and data-age is non-negative
    times = [rec["event_time"] for rec in records]
    assert times == sorted(times)
    for rec in records:
        assert rec["received_time"] >= rec["event_time"]


def test_scenario_tags_regime_through_adapter():
    records = list(TwinAdapter(CONFIG, horizon_min=HORIZON, scenario="fog_regime").stream())
    assert records and all(r["regime"] == "fog" for r in records)
    assert all(event_errors(r) == [] for r in records)
