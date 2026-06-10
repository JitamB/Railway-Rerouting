# `services/worker/` — Pipeline Orchestrator

The long-running stream consumer that walks the runtime pipeline for each disruption and owns
the graceful-degradation behaviour. This is the "brain stem" connecting the layers.

## Modules (`cascadeguard_worker/`)
| Module | Responsibility |
|---|---|
| `pipeline.py` | Consume validated events → k-hop subgraph → ST-GNN → trigger → re-route → alert. **Event-driven** recompute of touched subgraphs only, not a global 60s tick ([audit-02 §1.5](../../docs/audit-02-architecture-deep-dive.md)) |
| `degradation.py` | **Graceful-degradation ladder** + staleness watermark ([audit-04 §1](../../docs/audit-04-flaws-edge-cases.md)) |

## Degradation ladder
`live feed → last-known-position dead-reckoning → schedule-only prior`. Every prediction
carries "based on data N seconds old"; never go blank, never present a confident wrong answer.
On stage we *demonstrate* this — kill the feed and show the system degrade instead of lying.
