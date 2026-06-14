"""Route a classified grievance to the appropriate authority.

Maps the agent's category to a department from the registry; on low classification confidence
it falls back to the general helpdesk rather than guessing a wrong department (a misroute is
worse than a clumsy summary).
"""

from __future__ import annotations

# Below this confidence we route to the general helpdesk rather than guess a department — a
# misroute (e.g. a medical emergency sent to Catering) is worse than a clumsy summary.
CONFIDENCE_THRESHOLD = 0.5


def route(category: str, confidence: float, authorities: list, default) -> "object":
    """Return the Authority for ``category``; fall back to ``default`` if unsure/unknown."""
    if confidence < CONFIDENCE_THRESHOLD:
        return default
    for authority in authorities:
        if authority.category == category:
            return authority
    return default
