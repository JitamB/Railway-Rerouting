"""Calibration + drift monitoring (audit-02 §4, audit-04 §5).

Logs predicted-vs-actual to produce a reliability curve ("our 70% predictions happen 70% of
the time") and a Brier score, and flags calibration drift that signals a stale graph/model.
Report metrics **regime-stratified** (fog/monsoon/normal) so failure isn't hidden in an
average (audit-04 §4).
"""

from __future__ import annotations


def reliability_curve(probs: "object", outcomes: "object", bins: int = 10) -> "object":
    """Return binned (predicted, observed) frequencies for the reliability plot."""
    ...


def brier_score(probs: "object", outcomes: "object") -> float:
    ...


def drift_flag(history: "object", window: int = 1000) -> bool:
    """True if recent calibration degraded enough to warrant a graph/model rebuild."""
    ...
