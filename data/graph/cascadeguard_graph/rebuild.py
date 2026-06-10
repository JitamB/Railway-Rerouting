"""Timetable-diff-triggered graph rebuild (audit-04 §5).

IR revises zonal timetables and adds/cancels/reschedules trains regularly. A static graph
silently goes stale; treat the timetable as a versioned input and rebuild on change. Drift
monitoring (ml/eval/calibration.py) flags a stale graph via a calibration drop.
"""

from __future__ import annotations


def diff_timetable(old_path: str, new_path: str) -> dict:
    """Return added/removed/changed services between two timetable versions."""
    ...


def rebuild_if_changed(graph_store: "object", old_path: str, new_path: str) -> bool:
    """Rebuild the graph when a timetable diff is detected; returns True if rebuilt."""
    ...
