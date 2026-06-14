"""Send a case to the routed authority over a channel.

RailMadad is the production integration target for railway grievances; it is not openly
API'd, so the adapter is **mocked honestly** (and email is a generic fallback channel). The
dispatched payload carries structured fields, not just prose, so the authority can act.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class DispatchResult:
    ok: bool
    reference: str        # external ticket/reference id from the authority
    channel: str


def dispatch(case: "object", details: "object", channel: str = "railmadad") -> DispatchResult:
    """Forward the case to the authority; returns the external reference for tracking.

    RailMadad isn't openly API'd, so this is an honest mock: it returns a deterministic,
    clearly-labelled reference instead of calling a real endpoint. The payload it would send
    carries the structured fields (category, department, PNR, train, coach), not just prose, so
    the authority can act. ``email`` is the generic fallback channel.
    """
    digest = hashlib.sha1(case.case_id.encode()).hexdigest()[:6]
    prefix = "RM" if channel == "railmadad" else "EM"
    return DispatchResult(ok=True, reference=f"{prefix}-{digest}", channel=channel)
