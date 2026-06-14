"""Close the loop — accepted re-routes feed back as demand (audit-04 §7).

The classic prediction-affects-outcome problem: recommendations change the system. Recording
acceptances lets the next allocation account for filling seats, so we don't recommend a train
into overcapacity.
"""

from __future__ import annotations

from collections import defaultdict

_accepted: dict[str, int] = defaultdict(int)


def record_acceptance(pnr: str, train_no: str) -> None:
    """Register an accepted re-route so it counts as demand on ``train_no``."""
    _accepted[train_no] += 1


def projected_demand(train_no: str) -> int:
    """Return seats already committed via accepted re-routes for ``train_no``."""
    return _accepted[train_no]


def reset() -> None:
    """Clear committed demand (per demo run / test isolation)."""
    _accepted.clear()
