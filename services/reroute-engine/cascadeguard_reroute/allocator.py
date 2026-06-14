"""Capacity-aware, congestion-safe allocation (audit-03 §6, audit-04 §7).

Pushing the same alternative to *every* affected passenger overloads it and causes a second
cascade. We assign each passenger to the feasible candidate with the lowest projected load
ratio (assigned / capacity), so passengers spread across alternatives in proportion to live
capacity — two passengers with the same disruption get different, feasible routes. Capacity is
discounted by already-accepted re-routes (the demand loop), and when nothing fits we return an
honest "WAIT" rather than recommending a full train.
"""

from __future__ import annotations

from dataclasses import dataclass

from .feedback import projected_demand


@dataclass
class Allocation:
    pnr: str
    train_no: str
    probability: float  # fractional assignment weight


def _train_no(candidate) -> str:
    return candidate.train_no if hasattr(candidate, "train_no") else candidate


def _arrival(candidate, fallback: float) -> float:
    return getattr(candidate, "arrives_dest_min", fallback)


def allocate(
    passengers: list[str],
    candidates: list["object"],
    capacity: dict[str, int],
) -> list[Allocation]:
    """Spread passengers across candidates within capacity; never exceed a train's seats."""
    order = sorted(
        candidates, key=lambda c: _arrival(c, candidates.index(c))
    )  # most attractive (earliest arrival) first
    trains = [_train_no(c) for c in order]
    # effective capacity = seats minus seats already committed via accepted re-routes
    remaining = {t: max(0, capacity.get(t, 0) - projected_demand(t)) for t in trains}
    assigned: dict[str, int] = {t: 0 for t in trains}

    allocations = []
    for pnr in passengers:
        feasible = [c for c in order if assigned[_train_no(c)] < remaining[_train_no(c)]]
        if not feasible:
            allocations.append(Allocation(pnr, "WAIT", 0.0))  # honest degrade, no overload
            continue
        chosen = min(feasible, key=lambda c: (assigned[_train_no(c)] + 1) / remaining[_train_no(c)])
        t = _train_no(chosen)
        assigned[t] += 1
        free = sum(remaining.values())
        allocations.append(Allocation(pnr, t, round(remaining[t] / free, 3) if free else 1.0))
    return allocations
