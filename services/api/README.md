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
| `helpline.py` | `POST /helpline/chat` | Helpline turn (text **or** regional-language audio) → agent reply + opened case (delegates to `services/helpline`) |
| `queries.py` | `GET /queries`, `GET /queries/{case_id}` | Passenger's past queries + status (resolved/pending) and case history |
| `ws.py` | `WS /ws/live` | Live cascade deltas to the dashboard (push deltas, not full state — audit-02 §1.5) |

`main.py` mounts the routers and exposes `GET /health`. Responses carry a **staleness
watermark** ("based on data N seconds old") so the UI can grey out stale predictions
([audit-04 §1](../../docs/audit-04-flaws-edge-cases.md)).

Privacy: PNRs are PII — consent + minimization, not stored beyond the journey
([audit-04 bonus](../../docs/audit-04-flaws-edge-cases.md)).

## Implementation status (Stage 7, Step 26 — done)
Run: `uvicorn cascadeguard_api.main:app --reload` (docs at `/docs`). Test: `pytest services/api/tests`.

- `config.py` ✅ `load_settings()` from env (Redis/DB URLs, host/port, `DISRUPTION_STATION`).
- `deps.py` ✅ `CascadeStore` + `get_prediction_store()` dependency. **Twin-first:** the store
  computes the current cascade on demand via `predict_from_station` and caches it (same read
  interface the worker will write to in production); torch is imported lazily so tests inject
  canned records and never load the ML stack. Lookups: `for_train`, `for_station`, `corridor`,
  each carrying the staleness `watermark`.
- routers ✅ `GET /cascade/{train_no}`, `GET /stations/{code}`, `GET /corridor/{zone}` (read
  through the store), `POST /reroute` (template-first guidance, PNR never persisted; LLM
  enrichment stays on the worker's async path), `WS /ws/live` (streams per-station **deltas** +
  a completion marker — not full state, audit-02 §1.5).
- **Step 32 (Stage 9) ✅** `POST /helpline/chat` (text or multipart audio → the helpline agent via
  `get_helpline_agent`) and `GET /queries[/{case_id}]` (owner-scoped case list + history) are now
  live, backed by `services/helpline` (in-memory case store, offline-capable).
- **Verify:** `GET /cascade/12301` returns live risk (BSB 0.87) + watermark; `/docs` lists the
  endpoints; the WS streams deltas. `/corridor/ECR` → `status: red`; `/reroute` → `12303`,
  Platform 4, AVL 69, "arrives BSB only 10 min later".
