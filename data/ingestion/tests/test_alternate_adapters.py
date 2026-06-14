from pathlib import Path

import pytest

from cascadeguard_ingest.adapters import get_adapter
from cascadeguard_ingest.adapters.ntes_scrape import NtesScrapeAdapter
from cascadeguard_ingest.adapters.weather_tsr import WeatherTsrAdapter
from cascadeguard_ingest.circuit_breaker import BreakerState, CircuitBreaker, CircuitOpenError
from cascadeguard_ingest.contracts import event_errors

CONFIG = str(
    Path(__file__).resolve().parents[2] / "simulator" / "config" / "section.example.yaml"
)


# --- CG_DATA_SOURCE swap: twin <-> coa_rtis, identical downstream shape ---

def test_data_source_swap_is_transparent_downstream():
    twin = list(get_adapter("twin", CONFIG, horizon_min=160).stream())
    coa = list(get_adapter("coa_rtis", CONFIG, horizon_min=160).stream())

    assert [e["source"] for e in twin] == ["twin"] * len(twin)
    assert [e["source"] for e in coa] == ["coa_rtis"] * len(coa)

    # same events, both contract-valid — downstream consumers can't tell them apart by shape
    assert [(e["train_no"], e["station"], e["delay_min"]) for e in twin] == \
           [(e["train_no"], e["station"], e["delay_min"]) for e in coa]
    for e in twin + coa:
        assert event_errors(e) == []


def test_unknown_source_rejected():
    with pytest.raises(ValueError):
        get_adapter("satellite", CONFIG)


# --- NTES off by default; breaker trips on errors ---

def test_ntes_disabled_yields_nothing():
    assert list(NtesScrapeAdapter(enabled=False).stream()) == []


def test_breaker_trips_then_recovers():
    now = [0.0]
    breaker = CircuitBreaker(fail_threshold=3, reset_after_s=10.0, clock=lambda: now[0])

    def boom():
        raise RuntimeError("scrape failed")

    for _ in range(3):
        with pytest.raises(RuntimeError):
            breaker.call(boom)
    assert breaker.state is BreakerState.OPEN

    # while OPEN the call is short-circuited (fn never runs)
    calls = []
    with pytest.raises(CircuitOpenError):
        breaker.call(lambda: calls.append(1))
    assert calls == []

    # after the reset window -> HALF_OPEN -> a success closes it
    now[0] = 11.0
    assert breaker.state is BreakerState.HALF_OPEN
    assert breaker.call(lambda: "ok") == "ok"
    assert breaker.state is BreakerState.CLOSED


def test_ntes_failures_trip_the_breaker():
    breaker = CircuitBreaker(fail_threshold=2)
    ntes = NtesScrapeAdapter(enabled=True, breaker=breaker, scrape_fn=lambda: (_ for _ in ()).throw(RuntimeError()))
    for _ in range(3):
        assert list(ntes.stream()) == []  # failures swallowed, system stays up
    assert breaker.state is BreakerState.OPEN


# --- weather -> regime label ---

def test_weather_regime_label():
    w = WeatherTsrAdapter()
    assert w.regime(["PNBE", "MGS"]) == "normal"
    w.set_regime("MGS", "fog")
    assert w.regime(["PNBE", "MGS"]) == "fog"
    with pytest.raises(ValueError):
        w.set_regime("MGS", "blizzard")
