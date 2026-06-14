"""Reusable building blocks for the ST-GNN (diffusion conv, temporal/dilated conv).

Kept separate so model variants (Graph WaveNet vs DCRNN) can share components.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import MessagePassing


class TemporalConv(nn.Module):
    """Gated dilated 1-D convolution (Graph WaveNet-style), length-preserving.

    Input/output shape ``[N, channels, T]``. The gated activation ``tanh(filter)·σ(gate)`` lets
    the model select which parts of the recent delay trajectory matter.
    """

    def __init__(self, channels: int, dilation: int, kernel_size: int = 3) -> None:
        super().__init__()
        pad = dilation * (kernel_size - 1) // 2
        self.filter = nn.Conv1d(channels, channels, kernel_size, padding=pad, dilation=dilation)
        self.gate = nn.Conv1d(channels, channels, kernel_size, padding=pad, dilation=dilation)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.tanh(self.filter(x)) * torch.sigmoid(self.gate(x))


class DiffusionConv(MessagePassing):
    """Diffusion convolution (DCRNN-style) — models delay as diffusion over the graph.

    Sums K diffusion steps of degree-normalized neighbor aggregation, each with its own learned
    weight. Used as the spatial operator when ``arch=dcrnn`` (diffusion ≈ cascade).
    """

    def __init__(self, channels: int, k_hops: int = 2) -> None:
        super().__init__(aggr="add")
        self.k_hops = k_hops
        self.lins = nn.ModuleList(nn.Linear(channels, channels, bias=False) for _ in range(k_hops + 1))

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        col = edge_index[1]
        deg = torch.zeros(x.size(0), dtype=x.dtype, device=x.device)
        deg.scatter_add_(0, col, torch.ones_like(col, dtype=x.dtype))
        norm = (1.0 / deg.clamp(min=1.0))[col]  # per-edge, by target degree

        out = self.lins[0](x)
        h = x
        for i in range(1, self.k_hops + 1):
            h = self.propagate(edge_index, x=h, norm=norm)
            out = out + self.lins[i](h)
        return F.relu(out)

    def message(self, x_j: torch.Tensor, norm: torch.Tensor) -> torch.Tensor:
        return norm.view(-1, 1) * x_j
