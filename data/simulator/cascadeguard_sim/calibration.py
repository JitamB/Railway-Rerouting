"""Calibrate the twin's baseline running against a static historical NTES dump.

The acquisition of fine-grained historical data is itself unsolved (audit-02 §3.8); we use
whatever dump is available, state its limits, and fit running times / dwell distributions so
the twin's *normal* day matches reality before scenarios are injected.
"""

from __future__ import annotations


def calibrate(network: "object", timetable: "object", dump_path: str) -> dict:
    """Fit running-time and dwell parameters to a historical dump.

    Returns a parameter dict consumed by ``SimulationEngine``.
    """
    ...
