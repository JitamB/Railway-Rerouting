from cascadeguard_notify.trigger import should_notify


def test_confident_large_cascade_fires():
    # high risk, high & narrow interval (confident), big passenger-minutes at stake
    assert should_notify(0.85, (25.0, 40.0), minutes_saved_est=1800, false_alarm_cost=200) is True


def test_low_confidence_small_delay_does_not_fire():
    # modest risk, interval anchored at zero (we're not even sure there's a delay)
    assert should_notify(0.30, (0.0, 12.0), minutes_saved_est=200, false_alarm_cost=200) is False


def test_uncertain_large_delay_is_discounted():
    # large upper bound but lower bound ~0 → low confidence → benefit discounted away
    assert should_notify(0.6, (0.0, 60.0), minutes_saved_est=1500, false_alarm_cost=300) is False


def test_high_false_alarm_cost_raises_the_bar():
    base = dict(risk=0.7, interval_min=(15.0, 25.0), minutes_saved_est=400)
    assert should_notify(**base, false_alarm_cost=50) is True
    assert should_notify(**base, false_alarm_cost=100000) is False
