"""Shared FastAPI dependencies — the live cascade store the read endpoints serve from.

In production the worker (Step 25) writes predictions to Redis/Timescale and the API reads them.
For the twin-first build the store computes the current cascade on demand from the ST-GNN
(``predict_from_station``) and caches it — same read interface, no running worker required. Torch
is imported lazily, so the API package (and its tests, which inject canned records) never pulls
the ML stack unless a real prediction is actually requested.
"""

from __future__ import annotations

from functools import lru_cache

from cascadeguard_sim.timetable import Timetable
from cascadeguard_reroute.routing import DEFAULT_SECTION_CONFIG

from .config import load_settings


def _watermark(data_age_s: float) -> str:
    # mirrors cascadeguard_worker.degradation.watermark (the UI staleness contract)
    return f"based on data {int(round(data_age_s))}s old"


@lru_cache(maxsize=1)
def _timetable() -> Timetable:
    return Timetable.from_yaml(DEFAULT_SECTION_CONFIG)


class CascadeStore:
    """Latest per-station cascade predictions + the lookups the routers need."""

    def __init__(self, records: list[dict] | None = None, station: str | None = None) -> None:
        self._records = records  # None => compute lazily from the twin
        self._station = station or load_settings().disruption_station

    def records(self) -> list[dict]:
        if self._records is None:
            from cascadeguard_ml.inference import predict_from_station  # lazy: torch only here
            self._records = [
                {
                    "station": c.station,
                    "cascade_risk": round(c.cascade_risk, 3),
                    "delay_mean_min": round(c.delay_mean_min, 1),
                    "delay_interval_min": [round(x, 1) for x in c.delay_interval_min],
                    "why": c.why,
                    "mode": c.mode,
                    "data_age_s": c.data_age_s,
                }
                for c in predict_from_station(self._station, verbose=False)
            ]
        return self._records

    def data_age_s(self) -> float:
        recs = self.records()
        return max((r["data_age_s"] for r in recs), default=0.0)

    def for_train(self, train_no: str) -> dict:
        """Downstream stations on this train's route that are at risk."""
        try:
            stops = set(_timetable().service(train_no).stops)
        except (KeyError, StopIteration):
            stops = None
        at_risk = [r for r in self.records() if stops is None or r["station"] in stops]
        return {
            "train_no": train_no,
            "stations": at_risk,
            "mode": _mode(at_risk),
            "data_age_s": self.data_age_s(),
            "watermark": _watermark(self.data_age_s()),
        }

    def for_station(self, code: str) -> dict:
        """Incoming trains at this station with delay probability + ETA-delay window."""
        rec = next((r for r in self.records() if r["station"] == code), None)
        incoming = [s.train_no for s in _timetable().services() if code in s.stops]
        return {
            "station": code,
            "cascade_risk": rec["cascade_risk"] if rec else 0.0,
            "delay_interval_min": rec["delay_interval_min"] if rec else [0.0, 0.0],
            "why": rec["why"] if rec else "no prediction",
            "incoming_trains": incoming,
            "mode": rec["mode"] if rec else "live",
            "data_age_s": self.data_age_s(),
            "watermark": _watermark(self.data_age_s()),
        }

    def corridor(self, zone: str) -> dict:
        """Aggregate zone health (the open Corridor Risk API)."""
        recs = self.records()
        risks = [r["cascade_risk"] for r in recs]
        max_risk = max(risks, default=0.0)
        status = "red" if max_risk >= 0.66 else "amber" if max_risk >= 0.33 else "green"
        return {
            "zone": zone,
            "max_risk": round(max_risk, 3),
            "mean_risk": round(sum(risks) / len(risks), 3) if risks else 0.0,
            "stations_at_risk": [r["station"] for r in recs if r["cascade_risk"] >= 0.33],
            "status": status,
            "data_age_s": self.data_age_s(),
            "watermark": _watermark(self.data_age_s()),
        }


def _mode(records: list[dict]) -> str:
    # never present a degraded prediction as live: surface the worst mode in the slice
    order = {"live": 0, "dead_reckoning": 1, "schedule_prior": 2}
    return max((r["mode"] for r in records), key=lambda m: order.get(m, 0), default="live")


_STORE = CascadeStore()


def get_prediction_store() -> CascadeStore:
    """FastAPI dependency: the latest-prediction store (overridden in tests with canned data)."""
    return _STORE


def get_redis():
    """Return a Redis connection for reading the live prediction stream."""
    import redis

    return redis.Redis.from_url(load_settings().redis_url, decode_responses=True)


@lru_cache(maxsize=1)
def _helpline_agent():
    from cascadeguard_helpline.agent import HelplineAgent  # lazy: only when the helpline is used

    return HelplineAgent()


def get_helpline_agent():
    """FastAPI dependency: the singleton helpline agent (overridable in tests)."""
    return _helpline_agent()
