# `shared/` — Cross-Service Contracts

The single definition of the messages that cross service boundaries, so the twin, ingestion,
ML, re-route engine, and API all agree on shape. Defined as JSON Schema (language-neutral —
Python services and the TS frontends both consume them).

| Schema | Describes |
|---|---|
| [schemas/events.schema.json](schemas/events.schema.json) | A normalized train-position / delay event (every adapter emits this), with **event-time + data-age** fields (audit-04 §9) |
| [schemas/prediction.schema.json](schemas/prediction.schema.json) | A per-station cascade prediction: risk, conformal interval, the "why", and the staleness watermark |
| [schemas/grievance.schema.json](schemas/grievance.schema.json) | A helpline grievance case: category, routed department, status lifecycle, and history |

Change a contract here, regenerate downstream models, and every service stays in sync.
