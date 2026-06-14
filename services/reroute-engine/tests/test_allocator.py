import pytest

from cascadeguard_reroute import feedback
from cascadeguard_reroute.allocator import Allocation, allocate
from cascadeguard_reroute.routing import find_alternatives


@pytest.fixture(autouse=True)
def _clean_feedback():
    feedback.reset()
    yield
    feedback.reset()


def test_two_passengers_get_different_feasible_routes():
    candidates = find_alternatives("PNBE", "BSB", after_min=5)  # 12303, 15049
    capacity = {"12303": 50, "15049": 50}

    allocs = allocate(["PNR-A", "PNR-B"], candidates, capacity)
    trains = {a.train_no for a in allocs}

    assert len(allocs) == 2
    assert len(trains) == 2                      # DIFFERENT routes — no herding
    assert "WAIT" not in trains                  # both feasible
    assert all(isinstance(a, Allocation) for a in allocs)


def test_never_exceeds_capacity_and_degrades_to_wait():
    candidates = find_alternatives("PNBE", "BSB", after_min=5)
    capacity = {"12303": 1, "15049": 1}          # only 2 seats total

    allocs = allocate(["A", "B", "C"], candidates, capacity)
    placed = [a for a in allocs if a.train_no != "WAIT"]
    waits = [a for a in allocs if a.train_no == "WAIT"]

    assert len(placed) == 2 and len(waits) == 1  # 3rd passenger honestly told to wait
    # no train over its capacity
    from collections import Counter
    counts = Counter(a.train_no for a in placed)
    assert all(counts[t] <= 1 for t in ("12303", "15049"))


def test_accepted_reroutes_feed_back_as_demand():
    candidates = find_alternatives("PNBE", "BSB", after_min=5)
    capacity = {"12303": 1, "15049": 1}

    # 12303's one seat is already taken by a previously-accepted re-route
    feedback.record_acceptance("PNR-prev", "12303")
    assert feedback.projected_demand("12303") == 1

    allocs = allocate(["PNR-new"], candidates, capacity)
    # 12303 is now full (1 seat - 1 committed) -> the new passenger must go to 15049
    assert allocs[0].train_no == "15049"
