"""Runtime pipeline orchestrator.

Consumes validated events from the buffer and walks: k-hop subgraph -> ST-GNN inference
(+ OOD fallback) -> cost-sensitive trigger -> capacity-aware re-route -> template-first alert
(+ async LLM) -> push / WS. Recompute is **event-scoped** (touched subgraphs only), not a
global tick (audit-02 §1.5). See docs/workflow.md Part A.

The heavy ML inference lives in ``cascadeguard_ml.inference`` (k-hop subgraph + ST-GNN + OOD
fallback); this module orchestrates it with the trigger, the reroute engine, the phrasing
templates and the push sender. ``predict_from_station`` is injected so a fast, torch-free stub
can drive the pipeline in tests.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from cascadeguard_ingest.adapters.twin_adapter import DEFAULT_EPOCH
from cascadeguard_llm.phrasing import enrich, render_template
from cascadeguard_llm.prompts import build_guidance_prompt
from cascadeguard_ml.spec import RISK_THRESHOLD
from cascadeguard_notify.fcm import FcmSender
from cascadeguard_notify.trigger import should_notify
from cascadeguard_reroute.allocator import allocate
from cascadeguard_reroute.routing import DEFAULT_SECTION_CONFIG, find_alternatives
from cascadeguard_reroute.ticketing import live_availability
from cascadeguard_sim.timetable import Timetable

from .degradation import Mode, select_mode, watermark, worse

# Per-train tunable; the passenger-minutes of annoyance a needless alert costs. The trigger
# fires only when expected minutes saved beat this (audit-02 §4) — not at a magic 65%.
FALSE_ALARM_COST = 5.0
DEMO_DEVICE_TOKEN = "demo-device-token"
DEMO_PNR = "DEMO-PNR"

# Delay-magnitude bands for the phrasing templates (minutes), matching templates/*.delay-bands.txt.
LOW_MAX, HIGH_MIN = 15.0, 40.0


def _data_age_s(event: dict) -> float:
    """Freshness bound = how late the data was when received (received_time - event_time)."""
    ev = datetime.fromisoformat(event["event_time"])
    rc = datetime.fromisoformat(event["received_time"])
    return max(0.0, (rc - ev).total_seconds())


def _event_min(event: dict) -> float:
    """Invert the twin adapter's epoch mapping back to sim-minutes (the disruption time)."""
    return (datetime.fromisoformat(event["event_time"]) - DEFAULT_EPOCH).total_seconds() / 60.0


def _band(delay_min: float) -> str:
    if delay_min < LOW_MAX:
        return "low"
    return "high" if delay_min >= HIGH_MIN else "medium"


def process_event(event: dict, *, predictor=None, llm_client=None, sender=None) -> dict:
    """Handle a single validated disruption event end-to-end.

    Returns a structured record of the decision (so it's testable + visualisable): the
    degradation mode, the destination cascade, whether we notified, the chosen alternative and
    the push id. ``predictor`` defaults to the real ST-GNN inference but can be stubbed.
    """
    if predictor is None:
        from cascadeguard_ml.inference import predict_from_station  # lazy: torch only when real
        predictor = predict_from_station

    origin = event["station"]
    train_no = event["train_no"]
    data_age_s = _data_age_s(event)
    after_min = _event_min(event)
    feed_mode = select_mode(data_age_s)

    cascades = predictor(origin)  # list[StationCascade], worst-first; k-hop + OOD fallback inside
    if not cascades:
        return _result(origin, train_no, feed_mode, data_age_s, notified=False, reason="no cascade")

    tt = Timetable.from_yaml(DEFAULT_SECTION_CONFIG)
    dest = tt.service(train_no).stops[-1]  # the passenger's destination = end of this train's run
    target = next((c for c in cascades if c.station == dest), cascades[0])
    mode = worse(feed_mode, Mode(target.mode))  # combine feed staleness + OOD fallback

    fire = should_notify(
        target.cascade_risk, target.delay_interval_min,
        minutes_saved_est=target.delay_mean_min, false_alarm_cost=FALSE_ALARM_COST,
    )
    if not fire:
        return _result(origin, train_no, mode, data_age_s, notified=False,
                       reason="below trigger", target=target)

    # Capacity-aware re-route: other trains origin -> dest after the disruption, spread by seats.
    candidates = [c for c in find_alternatives(origin, dest, after_min) if c.train_no != train_no]
    capacity = {c.train_no: live_availability(c.train_no).seats for c in candidates}
    alloc = allocate([DEMO_PNR], candidates, capacity)
    chosen = next((c for c in candidates if c.train_no == alloc[0].train_no), None)

    if chosen is None:  # nothing feasible — honest "hold", never herd onto a full train
        body = f"Your {train_no} to {dest} is at risk and no seats are free on alternatives yet. Please hold; we'll re-check."
        msg_id = (sender or FcmSender()).send(DEMO_DEVICE_TOKEN, f"Delay alert — {train_no}", body)
        return _result(origin, train_no, mode, data_age_s, notified=True, reason="no feasible alt",
                       target=target, alert=body, push_id=msg_id, chosen="WAIT")

    avail = live_availability(chosen.train_no)
    sched_arr = tt.service(train_no).sched_arr_min.get(dest)
    delta_min = round(chosen.arrives_dest_min - sched_arr) if sched_arr is not None else round(target.delay_mean_min)
    fields = {
        "train_no": train_no,
        "delay_min": round(target.delay_mean_min),
        "risk_pct": round(target.cascade_risk * 100),
        "threshold": round(RISK_THRESHOLD),
        "alt_train": chosen.train_no,
        "alt_platform": chosen.platform,
        "alt_depart": f"+{round(chosen.departs_min - after_min)} min",
        "alt_eta": f"{round(chosen.arrives_dest_min - after_min)} min",
        "dest": dest,
        "delta_min": delta_min,
        "seats_status": f"{avail.status} {avail.seats}",
    }
    band = _band(target.delay_mean_min)
    template_text = render_template(band, "en", fields)

    body = template_text
    if llm_client is not None:  # optional async enrichment; alert already shipped from template
        prompt = build_guidance_prompt(origin, dest, target.delay_mean_min, target.cascade_risk, [chosen])
        body = asyncio.run(enrich(template_text, prompt, llm_client,
                                  safety_fields=[chosen.train_no, chosen.platform]))

    sender = sender or FcmSender()
    msg_id = sender.send(
        DEMO_DEVICE_TOKEN, f"Re-route suggested — {train_no}", body,
        data={"train_no": train_no, "alt_train": chosen.train_no, "platform": chosen.platform},
    )
    return _result(origin, train_no, mode, data_age_s, notified=True, reason="triggered",
                   target=target, alert=body, push_id=msg_id, chosen=chosen.train_no, band=band)


def _result(origin, train_no, mode, data_age_s, *, notified, reason,
            target=None, alert=None, push_id=None, chosen=None, band=None) -> dict:
    rec = {
        "station": origin, "train_no": train_no,
        "mode": mode.value, "watermark": watermark(data_age_s),
        "notified": notified, "reason": reason,
    }
    if target is not None:
        rec["dest_risk"] = round(target.cascade_risk, 3)
        rec["dest_delay_min"] = round(target.delay_mean_min, 1)
        rec["dest_interval_min"] = [round(x, 1) for x in target.delay_interval_min]
        rec["dest_station"] = target.station
        rec["why"] = target.why
    if band is not None:
        rec["band"] = band
    if alert is not None:
        rec["alert"] = alert
    if chosen is not None:
        rec["chosen"] = chosen
    if push_id is not None:
        rec["push_id"] = push_id
    return rec


def run() -> None:
    """Main consume loop; blocks, processing validated events from the buffer as they arrive."""
    import os

    from cascadeguard_ingest.buffer.store_forward import StoreForwardBuffer

    buf = StoreForwardBuffer(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        os.getenv("STREAM_KEY", "cascadeguard.events"),
    )
    for event in buf.consume("worker", "worker-1", block_ms=5000):
        try:
            process_event(event)
        finally:
            buf.ack("worker", event["_stream_id"])  # at-least-once: ack only after processing


if __name__ == "__main__":
    run()
