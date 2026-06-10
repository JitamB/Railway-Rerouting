# `data/ingestion/` — Adapters, Validation Gate, Buffer

Turns raw sources into a clean, event-time-stamped stream the models can trust. The ingestion
layer is where the audit's hardest reliability findings are addressed.

## Adapters (`cascadeguard_ingest/adapters/`)
The data layer must **not** be a single SPOF on one feed ([audit-02 §1.1](../../docs/audit-02-architecture-deep-dive.md)).

| Adapter | Role |
|---|---|
| `twin_adapter.py` | **Primary** — reads events from the digital twin |
| `coa_rtis_adapter.py` | **Production path (mocked)** — the real RTIS→COA integration point |
| `ntes_scrape.py` | **Optional enrichment** — behind a circuit-breaker; ToS-grey, off by default |
| `weather_tsr.py` | Weather as a **regime variable** + caution-order / TSR signals ([audit-04 §4](../../docs/audit-04-flaws-edge-cases.md)) |

## Validation gate (`cascadeguard_ingest/validation/`)
Nothing reaches the model unchecked — phantom cascades come from bad input
([audit-04 §3/§8](../../docs/audit-04-flaws-edge-cases.md)).

| Module | Role |
|---|---|
| `anomaly_gate.py` | Schema, de-dup, monotonic event-time, physical plausibility (`Δpos ≤ vmax·Δt`); quarantine to dead-letter |
| `map_matching.py` | Snap GPS to the track graph + Kalman/particle smoothing; reject teleports |

## Buffer & resilience
| Module | Role |
|---|---|
| `buffer/store_forward.py` | Redis Streams store-and-forward so transient gaps don't lose events ([audit-04 §1](../../docs/audit-04-flaws-edge-cases.md)) |
| `circuit_breaker.py` | Trip the optional NTES scrape on rate-limit/errors so it never takes the system down |

**Event-time semantics** ([audit-04 §9](../../docs/audit-04-flaws-edge-cases.md)): every event
carries when the train was *actually* there + a watermark, never "now − scheduled".
