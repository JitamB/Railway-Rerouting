from cascadeguard_reroute.ticketing import Availability, is_ticket_valid_on, live_availability


def test_reserved_ticket_not_valid_on_arbitrary_alternative():
    assert is_ticket_valid_on("12301", "12303") is False   # different train -> not valid
    assert is_ticket_valid_on("12301", "15049") is False
    assert is_ticket_valid_on("12301", "12301") is True     # same train -> valid


def test_live_availability_is_deterministic_and_well_formed():
    a = live_availability("12303")
    assert isinstance(a, Availability)
    assert a.status in ("AVL", "WL", "TATKAL", "FULL")
    assert a.seats >= 0
    assert a == live_availability("12303")   # deterministic


def test_status_matches_seat_count():
    for train in ["12301", "12302", "12303", "15049", "22222", "10000"]:
        a = live_availability(train)
        if a.seats == 0:
            assert a.status == "FULL"
        elif a.seats <= 12:
            assert a.status == "WL"
        else:
            assert a.status == "AVL"
