import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from cascadeguard_sim.engine import SimulationEngine
from cascadeguard_sim.network import SectionNetwork
from cascadeguard_sim.timetable import Timetable

ROOT = Path(__file__).resolve().parents[3]
CONFIG = Path(__file__).resolve().parents[1] / "config" / "section.example.yaml"
EVENT_SCHEMA = json.loads((ROOT / "shared" / "schemas" / "events.schema.json").read_text())

EPOCH = datetime(2026, 6, 12, 6, 0, tzinfo=timezone.utc)


def _to_record(ev) -> dict:
    """Map a sim-domain TrainEvent onto the wire contract (the twin adapter formalizes this)."""
    event_dt = EPOCH + timedelta(minutes=ev.event_time)
    return {
        "train_no": ev.train_no,
        "station": ev.station,
        "event_time": event_dt.isoformat(),
        "received_time": (event_dt + timedelta(seconds=30)).isoformat(),
        "delay_min": ev.delay_min,
        "source": "twin",
    }


def _engine() -> SimulationEngine:
    net = SectionNetwork.from_yaml(str(CONFIG))
    tt = Timetable.from_yaml(str(CONFIG))
    return SimulationEngine(net, tt)


def test_run_yields_schema_valid_event_stream():
    events = list(_engine().run(horizon_min=120))

    # a stream exists
    assert len(events) > 0

    # event-time ordering (audit-04 §9 — event-time semantics)
    times = [e.event_time for e in events]
    assert times == sorted(times)

    # every event validates against the frozen contract
    validator = Draft202012Validator(EVENT_SCHEMA)
    for ev in events:
        errors = list(validator.iter_errors(_to_record(ev)))
        assert not errors, f"{ev} -> {[e.message for e in errors]}"


def test_baseline_is_on_time():
    events = list(_engine().run(horizon_min=120))
    # No disruption injected: the twin reproduces the timetable, so nothing is late.
    assert max(e.delay_min for e in events) == 0
    assert min(e.delay_min for e in events) == 0


def test_determinism():
    a = [(e.train_no, e.station, e.event_time) for e in _engine().run(horizon_min=120)]
    b = [(e.train_no, e.station, e.event_time) for e in _engine().run(horizon_min=120)]
    assert a == b
