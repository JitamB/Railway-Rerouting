"""Reusable building blocks for the ST-GNN (diffusion conv, temporal/dilated conv, attention).

Kept separate so model variants (Graph WaveNet vs DCRNN vs TGN) can share components.
"""

from __future__ import annotations


class DiffusionConv:
    """Diffusion convolution step (DCRNN-style) — models delay as diffusion over the graph."""

    def __init__(self, channels: int, k_hops: int) -> None:
        ...


class TemporalConv:
    """Dilated temporal convolution (Graph WaveNet-style)."""

    def __init__(self, channels: int, dilation: int) -> None:
        ...
