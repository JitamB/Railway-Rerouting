"""End-to-end demo scenarios — the five things we show on stage, all on the digital twin with
**no live network**. Each maps to a claim in the definition-of-done / the audit's killer
questions. Running `pytest tests/e2e` is the cold rehearsal.

  1. replay-a-cascade          → a twin disruption flows through the full pipeline to a push
  2. two-passengers-reroute    → same disruption, different feasible routes (no herding)
  3. kill-the-feed-degrades    → live → dead-reckoning → schedule-prior, watermark never blank
  4. teleporting-GPS-quarantined → the validation gate dead-letters an impossible jump
  5. spoken-grievance-routes   → a regional-language complaint → routed, tracked case
"""

from cascadeguard_helpline.agent import HelplineAgent
from cascadeguard_helpline.cases import get_case
from cascadeguard_ingest.adapters.twin_adapter import TwinAdapter
from cascadeguard_ingest.validation.anomaly_gate import AnomalyGate
from cascadeguard_reroute.allocator import allocate
from cascadeguard_reroute.feedback import reset
from cascadeguard_reroute.routing import DEFAULT_SECTION_CONFIG, find_alternatives
from cascadeguard_reroute.ticketing import live_availability
from cascadeguard_worker.degradation import Mode, select_mode, watermark
from cascadeguard_worker.pipeline import process_event


def _event(train_no: str, station: str, event_time: str) -> dict:
    return {
        "train_no": train_no,
        "station": station,
        "event_time": event_time,
        "received_time": event_time,
        "delay_min": 0.0,
        "source": "twin",
    }


# 1 ─────────────────────────────────────────────────────────────────────────────────────────
def test_replay_cascade_flows_all_the_way_to_a_push():
    """A twin-injected OHE failure at MGS cascades downstream and reaches a passenger push."""
    events = list(TwinAdapter(DEFAULT_SECTION_CONFIG, scenario="ohe_failure").stream())
    trigger = max(
        (e for e in events if e["station"] == "MGS" and e["delay_min"] > 0),
        key=lambda e: e["delay_min"],
    )
    result = process_event(trigger)  # ingestion event → ST-GNN inference → trigger → reroute → push

    assert result["notified"] is True
    assert result["dest_risk"] > 0.5                 # downstream Varanasi (BSB) lit up before failing
    assert result["chosen"] in {"12303", "15049"}    # a feasible alternative was selected
    assert result["push_id"].startswith("mock-fcm-")
    assert result["mode"] == "live" and result["watermark"]


# 2 ─────────────────────────────────────────────────────────────────────────────────────────
def test_two_passengers_get_different_feasible_reroutes():
    """Same disruption → the allocator spreads passengers across alternatives (no second cascade)."""
    reset()  # clear the demand-feedback loop
    candidates = [c for c in find_alternatives("MGS", "BSB", 0.0) if c.train_no != "12301"]
    capacity = {c.train_no: live_availability(c.train_no).seats for c in candidates}

    allocations = allocate(["PAX-A", "PAX-B"], candidates, capacity)
    trains = [a.train_no for a in allocations]

    assert "WAIT" not in trains          # both passengers got a feasible seat
    assert len(set(trains)) == 2         # different trains — capacity-aware, no herding


# 3 ─────────────────────────────────────────────────────────────────────────────────────────
def test_kill_the_feed_degrades_gracefully():
    """As data goes stale the system steps down the ladder and always shows a watermark."""
    assert select_mode(30) is Mode.LIVE
    assert select_mode(300) is Mode.DEAD_RECKONING
    assert select_mode(900) is Mode.SCHEDULE_PRIOR
    assert all(watermark(age) for age in (30, 300, 900))  # never silently blank


# 4 ─────────────────────────────────────────────────────────────────────────────────────────
def test_teleporting_gps_fix_is_quarantined():
    """An impossible position jump is dead-lettered, so no phantom cascade reaches the graph."""
    station_km = {"PNBE": 0.0, "MGS": 210.0, "BSB": 228.0}
    gate = AnomalyGate(vmax_kmph=160.0, station_km=station_km)
    prev = _event("12301", "PNBE", "2026-06-12T06:00:00+00:00")

    teleport = _event("12301", "MGS", "2026-06-12T06:00:01+00:00")  # 210 km in 1 second
    res = gate.check(teleport, prev)
    assert res.ok is False and "implausible speed" in (res.reason or "")
    gate.quarantine(teleport, res.reason or "")
    assert len(gate.dead_letter) == 1

    plausible = _event("12301", "MGS", "2026-06-12T07:30:00+00:00")  # 210 km in 1.5 h ≈ 140 km/h
    assert gate.check(plausible, prev).ok is True


# 5 ─────────────────────────────────────────────────────────────────────────────────────────
def test_spoken_grievance_routes_to_the_right_authority():
    """A spoken regional-language complaint becomes a routed, trackable case."""
    reply = HelplineAgent().handle(
        "e2e_pax", audio="B4 coach mein ek lawaris bag pada hai".encode("utf-8"), language="hi"
    )
    assert "RPF" in reply.authority and reply.status == "open"

    case = get_case(reply.case_id)
    assert case is not None and case.category == "security" and case.input_mode == "speech"
