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


# Structural (non-cascade) relation connecting a service to the stations it stops at, so the
# GNN can pass messages between station and service nodes. Not a cascade edge type.
SERVES = "serves"

# Per-node and per-edge feature names referenced by builder.py and the ml data module.
STATION_FEATURES = ("platforms", "incoming_density", "regime")
SERVICE_FEATURES = ("n_stops", "max_delay_min")
EDGE_FEATURES = ("scheduled_delta_min", "min_turnaround_min")

# Canonical (src_node, relation, dst_node) triples the builder emits and the model consumes.
# Every cascade EdgeType appears here; SERVES is the structural connector.
CANONICAL_RELATIONS = (
    ("station", EdgeType.BLOCK_CONFLICT.value, "station"),
    ("service", EdgeType.PLATFORM_CONFLICT.value, "service"),
    ("service", EdgeType.RAKE_LINK.value, "service"),
    ("service", EdgeType.CREW_LINK.value, "service"),
    ("service", EdgeType.LOCO_LINK.value, "service"),
    ("service", SERVES, "station"),
)
