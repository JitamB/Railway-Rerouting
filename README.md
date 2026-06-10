# CascadeGuard 🚆

**Real-Time Delay-Cascade Predictor & Proactive Passenger Re-Routing Engine for Indian Railways.**

> *No consumer app models the network **cascade**, and none re-routes you **before** the railway announces the delay. That's CascadeGuard.*

A single delay propagates: a late train holds a platform, blocks the next arrival, pushes a
freight crossing, holds a third train. CascadeGuard models that cascade on a heterogeneous
station-dependency graph, predicts downstream risk with a spatio-temporal GNN, and pushes
**capacity-aware, ticketing-realistic** re-routes to passengers *before* the official delay
is announced.

## Documentation (read in this order)

1. [docs/problem-statement.md](docs/problem-statement.md) — authoritative problem + architecture
2. [docs/workflow.md](docs/workflow.md) — runtime pipeline + team build sequence
3. [intuition.md](intuition.md) — original v0 vision (superseded where it conflicts with the audit)
4. [docs/audit-00-verdict.md](docs/audit-00-verdict.md) — audit verdict + action plan (start here for the audit)

## Repository layout

| Path | Responsibility |
|---|---|
| [data/](data/) | Digital twin (primary data), ingestion + validation gate, dependency graph |
| [ml/](ml/) | One spatio-temporal GNN, conformal uncertainty, explainability, OOD, eval |
| [services/](services/) | FastAPI API, capacity-aware re-route engine, LLM phrasing, **helpline (grievance chatbot)**, notifier, worker |
| [frontend/](frontend/) | Passenger PWA (primary, incl. helpline + my-queries) + operator dashboard (context) |
| [shared/](shared/) | Cross-service event & prediction schemas |
| [infra/](infra/) | Docker, Redis, TimescaleDB, setup/demo scripts |
| [iot/](iot/) | Phase-2 edge-node schematic (optional) |
| [tests/](tests/) | Cross-service integration / e2e |

Each directory has its own `README.md` describing what to build there and which audit risk it closes.

## Status

**Scaffold (runnable skeleton).** Structure, manifests, and stubs exist; product logic is not
yet implemented. See `WHAT_WE_BUILT.md` (added in Phase 5) for the honest real / mocked / next
declaration.

## Quick start (skeleton)

```bash
cp .env.example .env          # fill in ANTHROPIC_API_KEY etc.
docker compose config         # validate the stack wiring
# Per-package dev install, e.g.:
pip install -e ml             # or data/simulator, services/api, ...
```

---

*CascadeGuard — FAR AWAY 2026 · Railways Track · Built with PyTorch Geometric · FastAPI · Next.js · Claude API · Indian Railways open data + a calibrated digital twin.*
