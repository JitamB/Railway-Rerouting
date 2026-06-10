"""The spatio-temporal GNN — CascadeGuard's single predictive core.

Replaces the v0 GNN+LSTM pair (audit-02 §1.3) with one model that handles space and time
jointly. Default arch: Graph WaveNet (learns the adjacency, fixing hand-set weights) or DCRNN
(diffusion ~ cascade). Outputs, per node: cascade risk, a delay distribution, and the basis
for a conformal interval.

Stubbed dependency-light so the package imports without torch installed.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NodePrediction:
    station: str
    cascade_risk: float          # 0..1
    delay_mean_min: float
    delay_interval_min: tuple[float, float]  # conformal interval


class SpatioTemporalGNN:
    """Graph WaveNet / DCRNN over a heterogeneous dependency graph."""

    def __init__(self, config: dict) -> None:
        ...

    def forward(self, subgraph: "object", history: "object") -> list[NodePrediction]:
        """Predict per-node cascade risk + delay distribution for a k-hop subgraph."""
        ...

    def load(self, checkpoint_path: str) -> "SpatioTemporalGNN":
        ...
