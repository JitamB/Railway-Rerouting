# `data/graph/` — Heterogeneous Station-Dependency Graph (Core IP)

The graph is CascadeGuard's defensible IP. v0 modelled **station-to-station** adjacency, which
is the *wrong physics* — cascade is driven by block/platform conflicts and, crucially,
**rake/crew/loco links** ([audit-02 §3.2](../../docs/audit-02-architecture-deep-dive.md)).
This package builds a **heterogeneous, multi-relational** graph instead.

## Edge types
`{ block-conflict, platform-conflict, rake-link, crew-link, loco-link }`

The **rake-link** (same physical trainset turning around as a later service) is a top cascade
source and a "we understand railways, not just graphs" credibility marker. Propagation weights
are **learned** end-to-end with the GNN, not hand-set
([audit-02 §3.4](../../docs/audit-02-architecture-deep-dive.md)).

## Modules (`cascadeguard_graph/`)
| Module | Responsibility |
|---|---|
| `schema.py` | Node/edge types, feature definitions, the `HeteroData` shape |
| `builder.py` | Build the graph from timetable + section topology |
| `store.py` | PyG sparse adjacency for the hot path; Memgraph/Neo4j option for scale/HA |
| `rebuild.py` | Timetable-diff-triggered rebuild when IR revises the timetable ([audit-04 §5](../../docs/audit-04-flaws-edge-cases.md)) |

Exports (GraphML / GeoJSON) land in `artifacts/`. Inference is **event-scoped** — only the
k-hop subgraph around a disruption, never a global recompute
([audit-04 §10](../../docs/audit-04-flaws-edge-cases.md)).

## Implementation status (Stage 3, Steps 11–13 — done)
Test: `pytest data/graph/tests`.

- `schema.py` ✅ node/edge types, `CANONICAL_RELATIONS`, feature names · `builder.py` ✅ networkx
  `MultiDiGraph` (HeteroData-compatible) with all five edge types + learned-weight placeholders +
  event-scoped `k_hop_subgraph` · `store.py` ✅ GraphML round-trip + GeoJSON export ·
  `rebuild.py` ✅ timetable-diff-triggered rebuild.
- Note: the package stays **framework-light** (networkx); the PyG `HeteroData` tensor conversion
  lives in `ml/cascadeguard_ml/training/data_module.py` (Step 14).
