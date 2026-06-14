"""Shared model/data spec — constants the data module, model, and eval all agree on.

Kept here so ``models/`` never imports ``training/`` (clean layering).
"""

from __future__ import annotations

from pathlib import Path

from cascadeguard_graph.schema import CANONICAL_RELATIONS

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SECTION_CONFIG = str(REPO_ROOT / "data" / "simulator" / "config" / "section.example.yaml")
DEFAULT_CHECKPOINT = str(REPO_ROOT / "ml" / "checkpoints" / "stgnn.pt")

# Temporal observation window: T samples over [cutoff-window, cutoff].
T = 8
OBS_CUTOFF = 62.0          # sim-min: inbound delays observed, outbound hasn't departed yet
OBS_WINDOW = 50.0
HORIZON = 160.0
RISK_THRESHOLD = 10.0      # min: "this train will be significantly delayed"
TAIL_THRESHOLD = 15.0      # min: a large (rare) cascade — what tail-recall measures

STATION_FEAT_DIM = 3       # platforms, incoming_density, regime
SERVICE_FEAT_DIM = 2       # n_stops, regime

NODE_TYPES = ["station", "service"]

# Message-passing relations. We flip the schema's ``serves`` to station->service so a station
# feeds its static capacity context into the trains calling there, WITHOUT ever carrying delay
# back (no service->station path). That keeps cross-train propagation on the service-service
# edges only — so the rake-link ablation stays clean.
SERVES_RELATION = ("station", "serves", "service")
RELATIONS = [tuple(r) for r in CANONICAL_RELATIONS if r[1] != "serves"] + [SERVES_RELATION]
RAKE_LINK_RELATION = ("service", "rake_link", "service")
