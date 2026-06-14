"""Graph persistence + the inference hot path.

Keeps the built graph in memory for fast k-hop inference, and exports GraphML (round-trippable)
/ GeoJSON (for map integrations). Pure in-memory networkx is fine for the demo; a Memgraph/Neo4j
backend is the scale/HA option, dropped beyond the demo (audit-02 §1.2).
"""

from __future__ import annotations

import json

import networkx as nx


class GraphStore:
    def __init__(self, backend: str = "pyg") -> None:  # "pyg" | "memgraph" | "neo4j"
        self.backend = backend
        self.graph: nx.MultiDiGraph | None = None  # the hot-path in-memory adjacency

    def set_graph(self, graph: nx.MultiDiGraph) -> None:
        """Replace the in-memory graph (used after a rebuild)."""
        self.graph = graph

    def load(self, artifact_path: str) -> nx.MultiDiGraph:
        graph = nx.read_graphml(artifact_path, force_multigraph=True)
        self.graph = graph
        return graph

    def export(self, graph: nx.MultiDiGraph, path: str, fmt: str = "graphml") -> None:
        """Export to GraphML / GeoJSON for downstream integrations."""
        if fmt == "graphml":
            nx.write_graphml(graph, path)
        elif fmt == "geojson":
            with open(path, "w") as fh:
                json.dump(self._to_geojson(graph), fh, indent=2)
        else:
            raise ValueError(f"unsupported export fmt {fmt!r} (expected graphml|geojson)")

    @staticmethod
    def _to_geojson(graph: nx.MultiDiGraph, coords: dict[str, tuple[float, float]] | None = None) -> dict:
        # Nodes as Features; geometry is set only when station coordinates are supplied
        # (the section config carries none — GPS coords are mocked until a real feed exists).
        coords = coords or {}
        features = []
        for node, data in graph.nodes(data=True):
            geometry = {"type": "Point", "coordinates": list(coords[node])} if node in coords else None
            features.append({"type": "Feature", "geometry": geometry,
                             "properties": {"id": node, **data}})
        return {"type": "FeatureCollection", "features": features}
