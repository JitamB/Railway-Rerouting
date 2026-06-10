"""Conformal prediction — distribution-free intervals with guaranteed coverage (audit-03 §4).

Wraps the ST-GNN point output to produce "90% of the time the true delay falls in [a, b]" and
the reliability curve that beats accuracy-only teams. Feeds the cost-sensitive notification
trigger (services/notifier).
"""

from __future__ import annotations


class ConformalCalibrator:
    def __init__(self, target_coverage: float = 0.90) -> None:
        ...

    def fit(self, residuals: "object") -> None:
        """Compute the conformal quantile from a calibration set."""
        ...

    def interval(self, point_pred: float) -> tuple[float, float]:
        """Return a coverage-guaranteed [lower, upper] delay interval."""
        ...
