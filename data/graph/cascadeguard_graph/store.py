"""Graph persistence + the inference hot path.

PyG sparse adjacency for fast k-hop inference; optional Memgraph/Neo4j backing when
persistence/HA/queries are needed at scale. Pure in-memory NetworkX is fine for the demo but
dropped beyond it (audit-02 §1.2).
"""

from __future__ import annotations


class GraphStore:
    def __init__(self, backend: str = "pyg") -> None:  # "pyg" | "memgraph" | "neo4j"
        ...

    def load(self, artifact_path: str) -> "object":
        ...

    def export(self, graph: "object", path: str, fmt: str = "graphml") -> None:
        """Export to GraphML / GeoJSON for downstream integrations."""
        ...
