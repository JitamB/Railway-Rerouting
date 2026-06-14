"""Cost-sensitive notification trigger (audit-02 §4).

Replaces the magic 65% threshold with a utility decision: fire when the expected
passenger-minutes saved exceed the expected cost of a false alarm, using the calibrated
conformal interval so the decision rests on known uncertainty.

We discount the benefit by an interval-derived confidence (lower/upper): a confident large
cascade has a high, narrow interval → confidence ≈ 1; a low-confidence small delay has an
interval whose lower bound is near zero → confidence ≈ 0, so it doesn't fire.
"""

from __future__ import annotations


def should_notify(
    risk: float,
    interval_min: tuple[float, float],
    minutes_saved_est: float,
    false_alarm_cost: float,
) -> bool:
    """Utility-based decision; True iff expected benefit > expected cost."""
    lo, hi = interval_min
    confidence = max(0.0, lo) / hi if hi > 0 else 0.0  # narrow/high interval → ~1; uncertain → ~0

    expected_benefit = risk * confidence * minutes_saved_est
    expected_cost = (1.0 - risk) * false_alarm_cost
    return expected_benefit > expected_cost
