"""Close the loop — accepted re-routes feed back as demand (audit-04 §7).

The classic prediction-affects-outcome problem: recommendations change the system. Recording
acceptances lets the next allocation account for filling seats, so we don't recommend a train
into overcapacity.
"""

from __future__ import annotations


def record_acceptance(pnr: str, train_no: str) -> None:
    """Register an accepted re-route so it counts as demand on ``train_no``."""
    ...


def projected_demand(train_no: str) -> int:
    """Return seats already committed via accepted re-routes for ``train_no``."""
    ...
