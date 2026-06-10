"""Re-route router — feasible alternatives for a passenger/PNR.

Delegates to the capacity-aware reroute-engine; never herds and never returns a full train
(audit-04 §7). PNR is PII — not persisted beyond the journey.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/reroute", tags=["reroute"])


@router.post("")
def reroute(pnr: str) -> dict:
    """Return capacity-feasible alternatives + plain-language guidance for ``pnr``."""
    ...
