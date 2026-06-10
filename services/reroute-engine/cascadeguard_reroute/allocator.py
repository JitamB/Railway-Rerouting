"""Capacity-aware, congestion-safe allocation (audit-03 §6, audit-04 §7).

Pushing the same alternative to *every* affected passenger overloads it and causes a second
cascade. Treat assignment as a capacity-constrained / congestion-game problem and recommend
**fractionally** across alternatives weighted by live capacity — so two passengers with the
same disruption get different, feasible routes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Allocation:
    pnr: str
    train_no: str
    probability: float  # fractional assignment weight


def allocate(
    passengers: list[str],
    candidates: list["object"],
    capacity: dict[str, int],
) -> list[Allocation]:
    """Spread passengers across candidates within capacity; never exceed a train's seats."""
    ...
