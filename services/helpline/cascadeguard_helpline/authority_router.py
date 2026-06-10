"""Route a classified grievance to the appropriate authority.

Maps the agent's category to a department from the registry; on low classification confidence
it falls back to the general helpdesk rather than guessing a wrong department (a misroute is
worse than a clumsy summary).
"""

from __future__ import annotations


def route(category: str, confidence: float, authorities: list, default) -> "object":
    """Return the Authority for ``category``; fall back to ``default`` if unsure/unknown."""
    ...
