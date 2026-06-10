"""Heterogeneous graph schema: node/edge types and feature definitions.

The shape consumed by the ST-GNN (ml/). Edge types encode the real physics of cascade, not
just station adjacency (audit-02 §3.2).
"""

from __future__ import annotations

from enum import Enum

NODE_TYPES = ("station", "service", "rake")


class EdgeType(str, Enum):
    BLOCK_CONFLICT = "block_conflict"
    PLATFORM_CONFLICT = "platform_conflict"
    RAKE_LINK = "rake_link"
    CREW_LINK = "crew_link"
    LOCO_LINK = "loco_link"


# Per-node and per-edge feature names referenced by builder.py and the ml data module.
STATION_FEATURES = ("platforms", "incoming_density", "regime")
EDGE_FEATURES = ("scheduled_delta_min", "min_turnaround_min")
