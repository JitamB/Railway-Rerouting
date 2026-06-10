# `services/api/` — FastAPI (REST + WebSocket + Corridor Risk API)

The serving front door. Async, OpenAPI auto-docs at `/docs`, WebSocket live feed for the
operator dashboard.

## Routers (`cascadeguard_api/routers/`)
| Router | Endpoint(s) | Purpose |
|---|---|---|
| `cascade.py` | `GET /cascade/{train_no}` | At-risk downstream stations for a train |
| `stations.py` | `GET /stations/{code}` | Incoming trains + delay probability + ETA range |
| `corridor.py` | `GET /corridor/{zone}` | Aggregate corridor health score (the open **Corridor Risk API**) |
| `reroute.py` | `POST /reroute` | Feasible alternatives for a passenger/PNR |
| `ws.py` | `WS /ws/live` | Live cascade deltas to the dashboard (push deltas, not full state — audit-02 §1.5) |

`main.py` mounts the routers and exposes `GET /health`. Responses carry a **staleness
watermark** ("based on data N seconds old") so the UI can grey out stale predictions
([audit-04 §1](../../docs/audit-04-flaws-edge-cases.md)).

Privacy: PNRs are PII — consent + minimization, not stored beyond the journey
([audit-04 bonus](../../docs/audit-04-flaws-edge-cases.md)).
