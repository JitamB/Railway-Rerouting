"""Graceful-degradation ladder + staleness watermark (audit-04 §1).

When the feed drops: live -> dead-reckoning (propagate along schedule at last-known speed) ->
schedule-only prior. Each step surfaces an explicit confidence drop and a data-age watermark.
Never go blank; never present a confident wrong answer.
"""

from __future__ import annotations

from enum import Enum


class Mode(str, Enum):
    LIVE = "live"
    DEAD_RECKONING = "dead_reckoning"
    SCHEDULE_PRIOR = "schedule_prior"


def select_mode(data_age_s: float) -> Mode:
    """Pick the degradation mode from how stale the latest data is."""
    ...


def watermark(data_age_s: float) -> str:
    """Render the 'based on data N seconds old' staleness label for the UI."""
    ...
