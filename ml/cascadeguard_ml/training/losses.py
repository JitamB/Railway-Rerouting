"""Tail-aware losses — the cascades that matter are rare (audit-04 §6).

Naive average loss is minimized by predicting "no cascade". Focal weighting (classification)
and a cost-sensitive Huber (regression) penalize missed large cascades heavily so the model
learns the tail, not the mean.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F

from cascadeguard_ml.spec import TAIL_THRESHOLD


def focal_loss(logits: torch.Tensor, target: torch.Tensor, gamma: float = 2.0,
               alpha: float = 0.25) -> torch.Tensor:
    """Focal loss for class-imbalanced cascade detection (binary, logits in)."""
    ce = F.binary_cross_entropy_with_logits(logits, target, reduction="none")
    p = torch.sigmoid(logits)
    p_t = p * target + (1 - p) * (1 - target)
    alpha_t = alpha * target + (1 - alpha) * (1 - target)
    return (alpha_t * (1 - p_t).pow(gamma) * ce).mean()


def cost_sensitive_loss(pred: torch.Tensor, target: torch.Tensor, miss_cost: float = 10.0,
                        tail_threshold: float = TAIL_THRESHOLD) -> torch.Tensor:
    """Penalize errors on large (tail) cascades by ``miss_cost`` relative to ordinary ones."""
    huber = F.smooth_l1_loss(pred, target, reduction="none")
    weight = 1.0 + (miss_cost - 1.0) * (target > tail_threshold).float()
    return (weight * huber).mean()
