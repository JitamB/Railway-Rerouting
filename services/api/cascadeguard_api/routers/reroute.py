"""Re-route router — feasible alternatives for a passenger/PNR.

Delegates to the capacity-aware reroute-engine; never herds and never returns a full train
(audit-04 §7). PNR is PII — not persisted beyond the journey.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from cascadeguard_llm.phrasing import render_template
from cascadeguard_reroute.routing import find_alternatives
from cascadeguard_reroute.ticketing import live_availability

from ..config import load_settings
from ..deps import CascadeStore, _timetable, get_prediction_store

router = APIRouter(prefix="/reroute", tags=["reroute"])

# Demo PNR -> journey. PNR is PII; never persisted beyond the request (audit-04 bonus). In
# production this resolves against the passenger's consented booking, not a static train.
DEMO_TRAIN, DEMO_DEST = "12301", "BSB"


@router.post("")
def reroute(pnr: str, store: CascadeStore = Depends(get_prediction_store)) -> dict:
    """Return capacity-feasible alternatives + template-first guidance for ``pnr``.

    Synchronous and offline-safe: guidance comes from the deterministic template; the LLM
    enrichment is the worker's async path, never the request path.
    """
    origin = load_settings().disruption_station   # where the passenger can still divert
    info = store.for_station(DEMO_DEST)
    current_risk = info["cascade_risk"]
    sched_arr = _timetable().service(DEMO_TRAIN).sched_arr_min.get(DEMO_DEST)

    options, top = [], None
    for c in find_alternatives(origin, DEMO_DEST, 0.0):
        if c.train_no == DEMO_TRAIN:
            continue
        avail = live_availability(c.train_no)
        opt = {
            "train_no": c.train_no, "platform": c.platform,
            "departs": f"{c.departs_min:.0f} min", "arrives_dest": f"{c.arrives_dest_min:.0f} min",
            "seats_status": f"{avail.status} {avail.seats}",
        }
        options.append(opt)
        top = top or (c, avail)

    if top is None:
        guidance = f"No feasible alternative to {DEMO_DEST} right now. Please hold; we'll re-check."
    else:
        c, avail = top
        delta = round(c.arrives_dest_min - sched_arr) if sched_arr is not None else "?"
        band = "high" if current_risk >= 0.66 else "medium" if current_risk >= 0.33 else "low"
        guidance = render_template(band, "en", {
            "train_no": DEMO_TRAIN, "risk_pct": round(current_risk * 100), "threshold": 10,
            "alt_train": c.train_no, "alt_platform": c.platform,
            "alt_depart": f"{c.departs_min:.0f} min", "alt_eta": f"{c.arrives_dest_min:.0f} min",
            "dest": DEMO_DEST, "delta_min": delta, "seats_status": f"{avail.status} {avail.seats}",
        })

    return {
        "pnr": pnr, "current_risk": current_risk, "options": options,
        "guidance": guidance, "watermark": info["watermark"],
    }
