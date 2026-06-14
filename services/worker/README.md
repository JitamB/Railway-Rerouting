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

## Implementation status (Stage 7, Step 25 — done)
Demo: `python services/worker/run_pipeline.py --scenario ohe_failure --station MGS` (add `--llm`
to enrich prose via Claude). Test: `pytest services/worker/tests`.

- `degradation.py` ✅ `select_mode(data_age_s)` (live ≤120s → dead-reckoning ≤600s → schedule
  prior), `worse(a, b)` (combine feed-staleness with the model's OOD fallback — never present
  the more confident of the two), `watermark(data_age_s)` → `"based on data Ns old"`.
- `pipeline.py` ✅ `process_event(event, *, predictor=, llm_client=, sender=)` walks
  inference → cost-sensitive `should_notify` → capacity-aware `find_alternatives`/`allocate`
  → template-first `render_template` (+ optional async `enrich`) → `FcmSender.send`, returning a
  structured decision record. The heavy ST-GNN (`predict_from_station`) is **injected** so tests
  drive the wiring torch-free. `run()` is the blocking buffer consumer (Redis Streams,
  at-least-once: ack only after processing).
- **Verify (🎯 checkpoint):** a twin-injected MGS OHE delay flows all the way to a push —
  `12301` delay 18 min → BSB risk 0.87 → trigger fires → re-route `15049` → templated alert →
  `mock-fcm-…` id, all on the twin.
