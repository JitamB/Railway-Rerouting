"""Timetable-diff-triggered graph rebuild (audit-04 §5).

IR revises zonal timetables and adds/cancels/reschedules trains regularly. A static graph
silently goes stale; treat the timetable as a versioned input and rebuild on change. Drift
monitoring (ml/eval/calibration.py) flags a stale graph via a calibration drop.
"""

from __future__ import annotations


def _services(path: str) -> dict:
    from cascadeguard_sim.timetable import Timetable

    return {
        s.train_no: (s.stops, s.sched_arr_min, s.sched_dep_min)
        for s in Timetable.from_yaml(path).services()
    }


def diff_timetable(old_path: str, new_path: str) -> dict:
    """Return added/removed/changed services between two timetable versions."""
    old, new = _services(old_path), _services(new_path)
    return {
        "added": sorted(set(new) - set(old)),
        "removed": sorted(set(old) - set(new)),
        "changed": sorted(t for t in set(old) & set(new) if old[t] != new[t]),
    }


def rebuild_if_changed(graph_store: "object", old_path: str, new_path: str) -> bool:
    """Rebuild the graph when a timetable diff is detected; returns True if rebuilt."""
    diff = diff_timetable(old_path, new_path)
    if not (diff["added"] or diff["removed"] or diff["changed"]):
        return False

    from cascadeguard_sim.network import SectionNetwork
    from cascadeguard_sim.timetable import Timetable

    from .builder import GraphBuilder

    graph = GraphBuilder(SectionNetwork.from_yaml(new_path), Timetable.from_yaml(new_path)).build()
    graph_store.set_graph(graph)
    return True
