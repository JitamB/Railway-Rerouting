"""Tail-aware losses — the cascades that matter are rare (audit-04 §6).

Naive average loss is minimized by predicting "no cascade". Focal / cost-sensitive weighting
penalizes missed large cascades heavily so the model learns the tail, not the mean.
"""

from __future__ import annotations


def focal_loss(pred: "object", target: "object", gamma: float = 2.0, alpha: float = 0.25):
    """Focal loss for class-imbalanced cascade detection."""
    ...


def cost_sensitive_loss(pred: "object", target: "object", miss_cost: float = 10.0):
    """Penalize missed large cascades by ``miss_cost`` relative to false alarms."""
    ...
