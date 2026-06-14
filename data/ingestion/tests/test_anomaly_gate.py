from cascadeguard_ingest.validation.anomaly_gate import AnomalyGate
from cascadeguard_ingest.validation.map_matching import MapMatcher, MatchedFix

# Cumulative km along the PNBE–MGS–BSB corridor (from the section block lengths).
STATION_KM = {"PNBE": 0.0, "MGS": 210.0, "BSB": 228.0}


def _ev(train, station, t, delay=0.0):
    return {
        "train_no": train,
        "station": station,
        "event_time": f"2026-06-12T{t}+00:00",
        "received_time": f"2026-06-12T{t}+00:00",
        "delay_min": delay,
        "source": "coa_rtis",
    }


def _gate():
    return AnomalyGate(vmax_kmph=160.0, station_km=STATION_KM)


def test_valid_progression_passes():
    gate = _gate()
    prev = _ev("12301", "PNBE", "06:00:00")
    # 210 km PNBE->MGS over 2 h = 105 km/h < 160 -> plausible
    cur = _ev("12301", "MGS", "08:00:00")
    assert gate.check(cur, prev).ok


def test_teleport_is_quarantined():
    gate = _gate()
    prev = _ev("12301", "PNBE", "06:00:00")
    # 210 km in 1 minute -> 12600 km/h -> impossible
    cur = _ev("12301", "MGS", "06:01:00")
    res = gate.check(cur, prev)
    assert not res.ok and "implausible speed" in res.reason

    gate.quarantine(cur, res.reason)
    assert gate.dead_letter == [(cur, res.reason)]


def test_duplicate_and_nonmonotonic_rejected():
    gate = _gate()
    e = _ev("12301", "MGS", "08:00:00")
    assert gate.check(e, e).reason == "duplicate"

    later = _ev("12301", "MGS", "08:00:00")
    earlier = _ev("12301", "PNBE", "07:00:00")
    assert gate.check(earlier, later).reason == "non-monotonic event-time"


def test_schema_violation_rejected():
    gate = _gate()
    bad = {"train_no": "12301", "station": "MGS"}  # missing required fields
    res = gate.check(bad, None)
    assert not res.ok and res.reason.startswith("schema:")


def test_twin_events_pass_without_positions():
    # No station_km -> the speed check is skipped; the trusted twin passes on schema+order.
    gate = AnomalyGate()
    prev = _ev("12301", "PNBE", "06:00:00")
    cur = _ev("12301", "MGS", "06:01:00")  # would be a "teleport" but no positions configured
    assert gate.check(cur, prev).ok


# --- map matching ---

CORRIDOR = [("PNBE", 25.60, 85.13), ("MGS", 25.28, 83.12), ("BSB", 25.32, 82.97)]


def test_ontrack_fix_high_confidence():
    mm = MapMatcher(CORRIDOR)
    fix = mm.match(25.28, 83.12, None)  # sitting on MGS
    assert fix.block_id == "MGS"
    assert fix.confidence > 0.8


def test_offtrack_fix_low_confidence_and_smoothed():
    mm = MapMatcher(CORRIDOR)
    prev = MatchedFix("PNBE", 0.0, 100.0, 0.95)
    fix = mm.match(28.6, 77.2, prev)  # a wild Delhi-ish fix far from the corridor
    assert fix.confidence < 0.1
    # the smoother stays near the prediction, not the teleported measurement
    assert fix.position_km < 50.0
