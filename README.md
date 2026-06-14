# CascadeGuard 🚆

**Real-Time Delay-Cascade Predictor & Proactive Passenger Re-Routing Engine for Indian Railways.**

> *No consumer app models the network **cascade**, and none re-routes you **before** the railway announces the delay. That's CascadeGuard.*

A single delay propagates: a late train holds a platform, blocks the next arrival, pushes a
freight crossing, holds a third train. CascadeGuard models that cascade on a heterogeneous
station-dependency graph, predicts downstream risk with a spatio-temporal GNN, and pushes
**capacity-aware, ticketing-realistic** re-routes to passengers *before* the official delay
is announced — plus a multilingual helpline that turns spoken grievances into routed, trackable
cases.

**Status: fully implemented.** All 10 build stages are complete — 108 tests pass, both frontends
typecheck, and the whole vertical slice runs **offline on a digital twin** (no live network, no
API keys). See [WHAT_WE_BUILT.md](WHAT_WE_BUILT.md) for the honest real / mocked / next breakdown.

---

## 1. What it does (the 30-second tour)

- **Predicts cascades**, not just one train's delay — a spatio-temporal GNN over a graph whose
  edges are *block, platform, rake, crew and loco* dependencies. Removing the rake-link edge drops
  tail-cascade recall **1.00 → 0.50** (the proof slide), so the topology measurably matters.
- **Re-routes proactively** — capacity-aware alternatives with real seat status (AVL/WL/FULL),
  spread across trains so the fix doesn't cause a second cascade, pushed *before* the announcement.
- **Knows what it doesn't know** — conformal prediction intervals, an OOD detector that falls back
  to a schedule prior, and a staleness watermark on every prediction ("based on data N s old").
- **Helps passengers** — a regional-language helpline (text or speech) routes grievances to the
  right authority (RPF, Medical, IRCTC…) and tracks each case to resolution.

---

## 2. Prerequisites

| Need | For | Notes |
|---|---|---|
| **Python 3.11** | backend, ML, the offline demo | the one hard requirement |
| **Node 18+ & npm** | the two frontends | only if you run the UIs |
| **Docker** (optional) | Redis + TimescaleDB in the full live stack | the demo does **not** need it |

No API keys are required for the demo. Groq (LLM), Firebase, Bhashini, OpenWeather etc. are all
**mocked / optional** and only activate when you supply keys in `.env`.

---

## 3. Quick start (offline demo — start here)

```bash
bash infra/scripts/setup.sh        # one-time: venv + editable installs + trains the model (~1-2 min)
bash infra/scripts/run_demo.sh     # the whole arc on the twin, no network, ~8s after setup
```

`run_demo.sh` walks the full vertical slice and prints a metric/visual at each step:

1. **Contracts locked** — every cross-service message validates against a frozen schema.
2. **Digital twin** — replays an OHE-failure cascade (PNBE → MGS → BSB).
3. **ST-GNN forecast** — downstream risk + calibrated interval + the one-line *why*.
4. **Worker pipeline** — a twin delay flows end-to-end to a passenger push.
5. **Helpline** — a spoken Hindi grievance → routed to RPF → tracked case.
6. **Five e2e scenarios** pass offline.

> First run trains the ST-GNN (the checkpoint is a build artifact, not in git). `setup.sh` does
> this for you; `run_demo.sh` also trains it if missing.

---

## 4. Running the live surfaces

The demo is self-contained, but you can also run the real services. Open separate terminals
(activate the venv first: `source .venv/bin/activate`).

### 4a. The API (REST + WebSocket + Corridor Risk API)

```bash
uvicorn cascadeguard_api.main:app --reload     # http://localhost:8000
```

Interactive docs at **http://localhost:8000/docs**. Twin-first: it computes predictions on demand
(no worker/DB required). Key endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | liveness |
| `GET` | `/cascade/{train_no}` | downstream stations at risk for a train (try `12301`) |
| `GET` | `/stations/{code}` | incoming trains + delay window at a station (try `MGS`, `BSB`) |
| `GET` | `/corridor/{zone}` | aggregate corridor health (the open Corridor Risk API) |
| `POST` | `/reroute?pnr=...` | capacity-feasible alternatives + plain-language guidance |
| `POST` | `/helpline/chat?passenger_id=...&text=...` | helpline turn (text or multipart `audio`) → routed case |
| `GET` | `/queries?passenger_id=...` | a passenger's past cases (owner-scoped) |
| `WS` | `/ws/live` | streams per-station cascade deltas to the dashboard |

```bash
# try it:
curl localhost:8000/cascade/12301
curl -X POST "localhost:8000/reroute?pnr=8412345678"
curl -X POST "localhost:8000/helpline/chat?passenger_id=me&text=unattended%20bag%20in%20B4"
```

### 4b. Operator dashboard (control-room web app)

```bash
cd frontend/operator-dashboard && npm install && npm run dev    # http://localhost:3001
```

With the API running, the corridor heatmap lights up **green → amber → red** live over the
WebSocket; click a station for the drill-down. API base is configurable via `VITE_API_BASE`
(default `http://localhost:8000`).

### 4c. Passenger app (Expo / React Native — the primary surface)

```bash
cd frontend/passenger-app && npm install && npx expo start      # scan the QR with Expo Go
```

Register a PNR (any value works in the demo) → see live risk and the re-route card; the Helpline
tab takes text or voice. **To run on a physical phone**, set `app.json` → `extra.apiBaseUrl` to
your machine's LAN IP (not `localhost`), since the phone can't reach `localhost`.

---

## 5. Individual demos & the proof slide

```bash
source .venv/bin/activate

python data/simulator/run_twin.py --scenario ohe_failure --horizon 160   # the digital twin
python -m cascadeguard_ml.inference --station MGS                         # ST-GNN cascade forecast
python services/worker/run_pipeline.py --scenario ohe_failure --station MGS  # twin delay → push
python -m cascadeguard_ml.eval.ablation                                   # rake-link proof: 0.50 → 1.00
```

---

## 6. Testing

```bash
source .venv/bin/activate
python shared/validate.py                  # contract validation → "ALL CONTRACTS LOCKED"
pytest data services ml tests              # full suite — 108 tests
pytest tests/e2e -q                        # just the 5 demo scenarios (offline)

# frontends
cd frontend/passenger-app   && npx tsc --noEmit     # typecheck
cd frontend/operator-dashboard && npx tsc --noEmit && npm run build
```

---

## 7. Configuration

Copy the template and fill in only what you want to switch from a mock to the real thing:

```bash
cp .env.example .env
```

| Variable | Switches on | Default behaviour |
|---|---|---|
| `GROQ_API_KEY` (+ `GROQ_MODEL`) | LLM phrasing of alerts/guidance (Groq, free tier) | template-only (offline) |
| `FCM_PROJECT_ID` + `FCM_CREDENTIALS_JSON` | real push delivery | `mock-fcm-…` ids |
| `ASR_PROVIDER` (`mock`/`groq`/`whisper`/`bhashini`) | real speech-to-text | clip decoded as text (mock) |
| `OPENWEATHER_API_KEY` | live weather/TSR regime | static regime |
| `CG_DATA_SOURCE` (`twin`/`coa_rtis`/`ntes`) | data source | `twin` (the primary, demo-safe source) |
| `REDIS_URL` / `DATABASE_URL` | Redis buffer / Postgres persistence | in-memory / twin-first |

Safety-critical fields (train no., platform, time, seats) always render from structured data —
the LLM only phrases the prose, never decides routing.

---

## Documentation (read in this order)

1. [docs/problem-statement.md](docs/problem-statement.md) — authoritative problem + architecture
2. [docs/workflow.md](docs/workflow.md) — runtime pipeline + team build sequence
3. [docs/implementation-guide.md](docs/implementation-guide.md) — step-by-step, file-by-file build order
4. [WHAT_WE_BUILT.md](WHAT_WE_BUILT.md) — **real / mocked / next** honesty declaration
5. [docs/audit-00-verdict.md](docs/audit-00-verdict.md) — audit verdict + action plan

## Repository layout

| Path | Responsibility |
|---|---|
| [data/](data/) | Digital twin (primary data), ingestion + validation gate, dependency graph |
| [ml/](ml/) | One spatio-temporal GNN, conformal uncertainty, explainability, OOD, eval |
| [services/](services/) | FastAPI API, capacity-aware re-route engine, LLM phrasing, **helpline (grievance chatbot)**, notifier, worker |
| [frontend/](frontend/) | Passenger app — **Expo/React Native** native (primary) + operator dashboard web (context) |
| [shared/](shared/) | Cross-service event & prediction schemas |
| [infra/](infra/) | Docker, Redis, TimescaleDB, setup/demo scripts |
| [tests/](tests/) | Cross-service integration / e2e (the demo scenarios) |

Each directory has its own `README.md` with an **Implementation status** section describing what
was built there and which audit risk it closes.

---

## 8. Troubleshooting

- **`run_demo.sh`: "checkpoint not found" / slow first run** — the ST-GNN trains on first use
  (~1-2 min); subsequent runs are instant. Re-run `setup.sh` to pre-train.
- **`python: command not found` / wrong version** — activate the venv: `source .venv/bin/activate`
  (must be Python 3.11; `python --version`).
- **Dashboard shows "Waiting for live feed"** — start the API (`uvicorn …`); the dashboard polls
  and reconnects automatically.
- **Passenger app can't reach the API on a phone** — set `app.json` → `extra.apiBaseUrl` to your
  LAN IP; `localhost` only works in a simulator/web preview.
- **CORS errors from the dashboard** — the API enables permissive CORS for the demo; make sure
  you're hitting the right `VITE_API_BASE`.

---

*CascadeGuard — FAR AWAY 2026 · Railways Track · Built with PyTorch Geometric · FastAPI · Expo / React Native · Groq (OpenAI-compatible LLM) · Indian Railways open data + a calibrated digital twin.*
