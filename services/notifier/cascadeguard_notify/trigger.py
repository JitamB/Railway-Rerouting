"""Cost-sensitive notification trigger (audit-02 §4).

Replaces the magic 65% threshold with a utility decision: fire when the expected
passenger-minutes saved exceed the expected cost of a false alarm, using the calibrated
conformal interval so the decision rests on known uncertainty.
"""

from __future__ import annotations


def should_notify(
    risk: float,
    interval_min: tuple[float, float],
    minutes_saved_est: float,
    false_alarm_cost: float,
) -> bool:
    """Utility-based decision; True iff expected benefit > expected cost."""
    ...
