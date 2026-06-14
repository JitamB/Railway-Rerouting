"""The spatio-temporal GNN — CascadeGuard's single predictive core.

Replaces the v0 GNN+LSTM pair (audit-02 §1.3) with one model handling space and time jointly:
a dilated temporal encoder over each node's recent delay trajectory feeds a heterogeneous
relational encoder (learned per-edge-type gates). Outputs, per service (train) node: cascade
risk + a delay point estimate (the basis for the conformal interval). Default arch: Graph
WaveNet; ``arch=dcrnn`` swaps in diffusion convolution.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F
from torch import nn

from cascadeguard_ml.spec import (
    NODE_TYPES,
    RELATIONS,
    SERVICE_FEAT_DIM,
    STATION_FEAT_DIM,
    T,
)

from .hetero import HeteroEncoder
from .layers import TemporalConv

_FEAT_DIM = {"station": STATION_FEAT_DIM, "service": SERVICE_FEAT_DIM}


@dataclass
class NodePrediction:
    station: str
    cascade_risk: float          # 0..1
    delay_mean_min: float
    delay_interval_min: tuple[float, float]  # conformal interval


class _TemporalEncoder(nn.Module):
    """Dilated temporal conv stack over a [N, T] delay trajectory -> [N, hidden]."""

    def __init__(self, hidden: int) -> None:
        super().__init__()
        self.in_proj = nn.Conv1d(1, hidden, kernel_size=1)
        self.tconv1 = TemporalConv(hidden, dilation=1)
        self.tconv2 = TemporalConv(hidden, dilation=2)

    def forward(self, history: torch.Tensor) -> torch.Tensor:
        x = self.in_proj(history.unsqueeze(1))   # [N, hidden, T]
        x = self.tconv1(x)
        x = self.tconv2(x)
        return x.mean(dim=-1)                      # global temporal pool -> [N, hidden]


class SpatioTemporalGNN(nn.Module):
    """Graph WaveNet / DCRNN over a heterogeneous dependency graph."""

    def __init__(self, config: dict | None = None) -> None:
        super().__init__()
        m = (config or {}).get("model", {})
        self.hidden = m.get("hidden_dim", 64)
        arch = m.get("arch", "graph_wavenet")
        layers = m.get("layers", 4)

        self.temporal = _TemporalEncoder(self.hidden)
        self.static_proj = nn.ModuleDict(
            {nt: nn.Linear(_FEAT_DIM[nt], self.hidden) for nt in NODE_TYPES}
        )
        self.encoder = HeteroEncoder(NODE_TYPES, RELATIONS, self.hidden, layers, arch)
        self.risk_head = nn.Linear(self.hidden, 1)
        self.delay_head = nn.Linear(self.hidden, 1)

    def _embed(self, data, return_contrib: bool = False):
        x_dict = {}
        for nt in NODE_TYPES:
            x_dict[nt] = F.relu(self.static_proj[nt](data[nt].x) + self.temporal(data[nt].history))
        return self.encoder(x_dict, data.edge_index_dict, return_contrib=return_contrib)

    def forward(self, data) -> dict:
        """Per-service cascade risk logits + delay point estimate (+ embeddings for OOD)."""
        emb = self._embed(data)
        h = emb["service"]
        return {
            "risk_logit": self.risk_head(h).squeeze(-1),
            "delay": self.delay_head(h).squeeze(-1),
            "embedding": h,
        }

    @torch.no_grad()
    def predict(self, data, names: list[str], calibrator=None) -> list[NodePrediction]:
        """Per-node NodePredictions; ``calibrator`` (conformal) widens the interval if given."""
        self.eval()
        out = self.forward(data)
        risk = torch.sigmoid(out["risk_logit"])
        delay = out["delay"]
        preds = []
        for i, name in enumerate(names):
            mean = float(delay[i])
            interval = calibrator.interval(mean) if calibrator is not None else (mean, mean)
            preds.append(NodePrediction(name, float(risk[i]), mean, interval))
        return preds

    def load(self, checkpoint_path: str) -> "SpatioTemporalGNN":
        ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        self.load_state_dict(ckpt["state_dict"])
        return self
