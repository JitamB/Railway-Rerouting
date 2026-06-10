"""Build the heterogeneous dependency graph from timetable + section topology.

Emits the multi-relational graph (PyG ``HeteroData``-compatible) with learned-weight
placeholders on each edge type. Edge weights are fit jointly with the GNN, never hand-set
(audit-02 §3.4).
"""

from __future__ import annotations


class GraphBuilder:
    def __init__(self, network: "object", timetable: "object") -> None:
        ...

    def build(self) -> "object":
        """Return a HeteroData-shaped graph with typed edges and node/edge features."""
        ...

    def k_hop_subgraph(self, node: str, k: int = 3) -> "object":
        """Event-scoped subgraph around a disruption (audit-04 §10)."""
        ...
