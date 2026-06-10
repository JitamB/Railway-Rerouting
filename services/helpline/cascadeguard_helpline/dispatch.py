"""Send a case to the routed authority over a channel.

RailMadad is the production integration target for railway grievances; it is not openly
API'd, so the adapter is **mocked honestly** (and email is a generic fallback channel). The
dispatched payload carries structured fields, not just prose, so the authority can act.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DispatchResult:
    ok: bool
    reference: str        # external ticket/reference id from the authority
    channel: str


def dispatch(case: "object", details: "object", channel: str = "railmadad") -> DispatchResult:
    """Forward the case to the authority; returns the external reference for tracking."""
    ...
