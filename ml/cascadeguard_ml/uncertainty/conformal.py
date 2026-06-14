"""Conformal prediction — distribution-free intervals with guaranteed coverage (audit-03 §4).

Split conformal: from a calibration set of absolute residuals we take the (finite-sample
corrected) quantile q, so [pred-q, pred+q] covers the truth at the target rate regardless of
the error distribution. Feeds the cost-sensitive notification trigger (services/notifier).
"""

from __future__ import annotations

import math

import numpy as np


class ConformalCalibrator:
    def __init__(self, target_coverage: float = 0.90) -> None:
        self.target_coverage = target_coverage
        self.q: float | None = None

    def fit(self, residuals) -> None:
        """Compute the conformal quantile from a calibration set of |y - pred|."""
        r = np.abs(np.asarray(residuals, dtype=float))
        n = len(r)
        if n == 0:
            raise ValueError("need a non-empty calibration set")
        # finite-sample correction: level = ceil((n+1)*coverage)/n, clipped to [0, 1]
        level = min(1.0, math.ceil((n + 1) * self.target_coverage) / n)
        self.q = float(np.quantile(r, level, method="higher"))

    def interval(self, point_pred: float) -> tuple[float, float]:
        """Return a coverage-guaranteed [lower, upper] delay interval (delay >= 0)."""
        if self.q is None:
            raise RuntimeError("call fit() before interval()")
        return (max(0.0, point_pred - self.q), point_pred + self.q)

    def coverage(self, preds, targets) -> float:
        """Empirical coverage of the fitted interval on a held-out set (for the reliability check)."""
        preds, targets = np.asarray(preds, dtype=float), np.asarray(targets, dtype=float)
        lo = np.maximum(0.0, preds - self.q)
        hi = preds + self.q
        return float(np.mean((targets >= lo) & (targets <= hi)))
