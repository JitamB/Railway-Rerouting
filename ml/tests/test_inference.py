from cascadeguard_ml.inference import StationCascade, predict_from_station


def test_predict_from_station_returns_cascade_vector():
    cascades = predict_from_station("MGS", verbose=False)

    assert cascades and all(isinstance(c, StationCascade) for c in cascades)
    for c in cascades:
        assert 0.0 <= c.cascade_risk <= 1.0
        lo, hi = c.delay_interval_min
        assert lo <= c.delay_mean_min <= hi
        assert c.mode in ("live", "schedule_prior")

    # PNBE is reached only via the rake-link (the outbound 12302) -> the moat shows up in the why
    pnbe = next(c for c in cascades if c.station == "PNBE")
    assert pnbe.cascade_risk > 0.5
    assert "rake-link" in pnbe.why
