from cascadeguard_worker.degradation import Mode, select_mode, watermark, worse


def test_select_mode_ladder():
    assert select_mode(30) is Mode.LIVE
    assert select_mode(300) is Mode.DEAD_RECKONING   # feed gap -> dead-reckoning
    assert select_mode(900) is Mode.SCHEDULE_PRIOR    # long gap -> schedule-only prior


def test_worse_takes_the_more_degraded_mode():
    # a live feed but an OOD model fallback must not be presented as "live"
    assert worse(Mode.LIVE, Mode.SCHEDULE_PRIOR) is Mode.SCHEDULE_PRIOR
    assert worse(Mode.DEAD_RECKONING, Mode.LIVE) is Mode.DEAD_RECKONING


def test_watermark_label():
    assert watermark(30) == "based on data 30s old"
