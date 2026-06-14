"""Graceful-degradation ladder + staleness watermark (audit-04 §1).

When the feed drops: live -> dead-reckoning (propagate along schedule at last-known speed) ->
schedule-only prior. Each step surfaces an explicit confidence drop and a data-age watermark.
Never go blank; never present a confident wrong answer.
"""

from __future__ import annotations

from enum import Enum

# Feed-staleness thresholds. Within LIVE_MAX_S the live feed is trusted; up to DEAD_RECKON_MAX_S
# we propagate the last-known position along the schedule; beyond that we fall back to the
# schedule-only prior. Tunable per section; these are sane single-zone defaults.
LIVE_MAX_S = 120.0
DEAD_RECKON_MAX_S = 600.0

# Severity order so two independent degradations (feed staleness + the model's OOD fallback)
# can be combined by taking the worse one — never present the more confident of the two.
_SEVERITY = {"live": 0, "dead_reckoning": 1, "schedule_prior": 2}


class Mode(str, Enum):
    LIVE = "live"
    DEAD_RECKONING = "dead_reckoning"
    SCHEDULE_PRIOR = "schedule_prior"


def select_mode(data_age_s: float) -> Mode:
    """Pick the degradation mode from how stale the latest data is."""
    if data_age_s <= LIVE_MAX_S:
        return Mode.LIVE
    if data_age_s <= DEAD_RECKON_MAX_S:
        return Mode.DEAD_RECKONING
    return Mode.SCHEDULE_PRIOR


def worse(a: Mode, b: Mode) -> Mode:
    """Return the more degraded of two modes (so we never over-state confidence)."""
    return a if _SEVERITY[a.value] >= _SEVERITY[b.value] else b


def watermark(data_age_s: float) -> str:
    """Render the 'based on data N seconds old' staleness label for the UI."""
    return f"based on data {int(round(data_age_s))}s old"
