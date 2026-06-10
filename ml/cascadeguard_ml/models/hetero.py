"""Heterogeneous message passing over the multi-relational dependency graph.

Relational layers (PyG ``HeteroConv`` / RGCN-style) with per-edge-type weights for
{block, platform, rake-link, crew, loco}. The rake-link relation is the high-value one
(audit-02 §3.2). Edge weights are learned jointly with the prediction objective.
"""

from __future__ import annotations


class HeteroEncoder:
    """Per-edge-type relational encoder feeding the temporal stack in stgnn.py."""

    def __init__(self, edge_types: list[str], hidden_dim: int) -> None:
        ...

    def forward(self, subgraph: "object") -> "object":
        """Return per-node embeddings aggregated across edge types."""
        ...
