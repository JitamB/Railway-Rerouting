from cascadeguard_reroute.routing import Candidate, find_alternatives


def test_disrupted_journey_returns_plausible_alternatives():
    # Passenger booked on 12301 (PNBE->BSB, dep 0) is disrupted at t=5; find later PNBE->BSB trains.
    alts = find_alternatives("PNBE", "BSB", after_min=5)
    trains = [c.train_no for c in alts]

    assert trains == ["12303", "15049"]          # the other down trains, 12301 excluded by time
    assert all(isinstance(c, Candidate) for c in alts)
    assert alts[0].arrives_dest_min <= alts[1].arrives_dest_min  # sorted by earliest arrival
    assert all(c.departs_min >= 5 for c in alts)


def test_respects_direction_and_topk():
    # only the up train serves BSB->PNBE
    up = find_alternatives("BSB", "PNBE", after_min=0)
    assert [c.train_no for c in up] == ["12302"]

    # k caps the result count
    assert len(find_alternatives("PNBE", "BSB", after_min=0, k=2)) == 2


def test_no_alternatives_after_last_departure():
    assert find_alternatives("PNBE", "BSB", after_min=999) == []
