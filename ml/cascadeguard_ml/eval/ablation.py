"""The single best proof slide: with-vs-without-rake-link ablation (audit-02 §3.4).

Trains/evaluates the model with and without the rake-link edge type and reports the delta on
**tail recall** (large-cascade events), proving the topology edges measurably matter rather
than just being decoration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AblationResult:
    variant: str           # "with_rake_link" | "without_rake_link"
    tail_recall: float
    brier: float


def run_ablation(config_path: str) -> list[AblationResult]:
    """Run both variants and return their tail-recall / Brier metrics for comparison."""
    ...
