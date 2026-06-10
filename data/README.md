# `data/` — Data Layer

Everything that produces, validates, and structures the events the models consume. This layer
exists because **there is no open real-time feed** for Indian Railways
([audit-01 §3](../docs/audit-01-screening-feasibility.md)) — so the **digital twin is the
primary source**, not a fallback.

| Subdirectory | Role | Closes |
|---|---|---|
| [simulator/](simulator/) | Discrete-event **digital twin** — primary data source, counterfactual engine, rare-event generator | audit-01 §3, audit-03 §2, audit-04 §2/§6 |
| [ingestion/](ingestion/) | Source **adapters** (twin / COA-RTIS-mock / NTES-scrape / weather-TSR), **validation/anomaly gate**, store-and-forward **buffer** | audit-02 §1.1, audit-04 §1/§3/§8/§9 |
| [graph/](graph/) | The **heterogeneous station-dependency graph** — the core IP | audit-02 §3.2/§3.4, audit-04 §5/§10 |
| [datasets/](datasets/) | Historical NTES dumps + calibration data (git-ignored) | audit-02 §3.8 |

**Flow:** `simulator` (or an adapter) emits events → `ingestion` buffers, stamps event-time,
and validates them → events traverse the `graph` for prediction. See
[../docs/workflow.md](../docs/workflow.md) Part A, stages 1–4.
