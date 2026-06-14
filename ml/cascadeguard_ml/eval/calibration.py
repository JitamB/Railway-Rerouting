"""Calibration + drift monitoring (audit-02 §4, audit-04 §5).

Logs predicted-vs-actual to produce a reliability curve ("our 70% predictions happen 70% of
the time") and a Brier score, and flags calibration drift that signals a stale graph/model.
Report metrics **regime-stratified** (fog/monsoon/normal) so failure isn't hidden in an
average (audit-04 §4).
"""

from __future__ import annotations

import numpy as np


def brier_score(probs, outcomes) -> float:
    probs, outcomes = np.asarray(probs, dtype=float), np.asarray(outcomes, dtype=float)
    return float(np.mean((probs - outcomes) ** 2))


def reliability_curve(probs, outcomes, bins: int = 10):
    """Return binned (mean_predicted, observed_frequency, count) for the reliability plot."""
    probs, outcomes = np.asarray(probs, dtype=float), np.asarray(outcomes, dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(probs, edges[1:-1]), 0, bins - 1)
    pred, obs, cnt = [], [], []
    for b in range(bins):
        m = idx == b
        if m.any():
            pred.append(float(probs[m].mean()))
            obs.append(float(outcomes[m].mean()))
            cnt.append(int(m.sum()))
    return np.array(pred), np.array(obs), np.array(cnt)


def drift_flag(history, window: int = 1000, ratio: float = 1.5, margin: float = 0.05) -> bool:
    """True if recent calibration (Brier over time) degraded enough to warrant a rebuild."""
    h = np.asarray(history, dtype=float)
    if len(h) < 2 * window:
        return False
    past, recent = h[-2 * window:-window].mean(), h[-window:].mean()
    return bool(recent > past * ratio + margin)
