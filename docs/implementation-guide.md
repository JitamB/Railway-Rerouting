# CascadeGuard — Implementation Guide (Step-by-Step Build Order)

The repo is fully scaffolded (every file exists as a stub). This guide is the **continuous
order in which to fill those stubs with real code** so that, at every step, everything a step
needs already exists, and everything it produces is consumed by a later step. You never build
something you can't yet test.

- The *what & why* lives in [problem-statement.md](problem-statement.md).
- The *high-level phases* live in [workflow.md](workflow.md) Part B.
- **This file is the fine-grained, file-by-file chain.** Each step says what it inherits from
  the previous step and what it hands to the next.

---

## How to read a step

```
### Step N — Title            · owner · stage
Files:    the stubs you fill in this step
← After:  what the previous step produced that this one stands on
→ Before: what the next step needs you to hand it
Do:       the concrete implementation
Verify:   the check that proves the step is done
```

Owners map to [problem-statement.md §11](problem-statement.md) (M1 ML model · M2 ML/data ·
M3 data eng · M4 frontend · M5 backend).

## Guiding principles (carry these through every step)
1. **Twin-first.** The digital twin is the spine; nothing on stage depends on a live network.
2. **Contracts-first.** Every boundary speaks the `shared/schemas` shapes — fill those meanings in first.
3. **Mock honestly.** COA/RTIS, IRCTC, Bhashini, RailMadad are stubbed behind clean adapters.
4. **Structured fields are authoritative; the LLM only phrases.** True for alerts *and* helpline.
5. **Vertical checkpoints.** At the 🎯 markers you can actually run/show something — don't skip them.

## The dependency spine
```
contracts ─► infra(redis,db) ─► TWIN ─► ingestion ─► graph ─► ML ─► reroute ─┐
                                                                              ▼
        frontend ◄─ API ◄─ WORKER (orchestrates) ◄─ notifier/llm ◄───────────┘
                                          │
                          helpline subsystem (parallel track) ─► helpline API ─► app screens
```

## Parallelization (after Stage 0)
The spine is sequential, but three tracks can run in parallel once contracts exist:
**M3** owns data (Stages 1–2), **M2/M1** own graph+ML (Stages 3–4) against twin sample dumps,
**M4** builds frontend against a mocked API, **M5** builds reroute→worker→API. The **helpline**
track (Stage 9) only needs the DB + contracts, so it can start early too.

---

# Stage 0 — Foundations & contracts

### Step 1 — Lock the data contracts · M5 · stage 0
**Files:** [shared/schemas/events.schema.json](../shared/schemas/events.schema.json), [prediction.schema.json](../shared/schemas/prediction.schema.json), [grievance.schema.json](../shared/schemas/grievance.schema.json)
**← After:** the scaffold (schemas exist as drafts).
**→ Before:** every producer/consumer in the repo validates against these, so freeze them now.
**Do:** finalize required fields, especially `event_time` vs `received_time` (data-age) on events
and `data_age_s`/`mode` on predictions. Generate Pydantic/TS types from them if you like.
**Verify:** a sample event and a sample prediction validate against their schema.

### Step 2 — Bring up infra (Redis + TimescaleDB) · M5 · stage 0
**Files:** [docker-compose.yml](../docker-compose.yml), [infra/db/init.sql](../infra/db/init.sql), [infra/redis/redis.conf](../infra/redis/redis.conf), [.env](../.env.example)
**← After:** contracts (the DB tables mirror them).
**→ Before:** Step 8's buffer needs Redis; Step 30's cases and Step 26's reads need Postgres.
**Do:** `cp .env.example .env`; create the `delay_events`, `predictions`, `grievance_cases`,
`grievance_events` tables (uncomment the hypertable calls).
**Verify:** `docker compose up -d redis timescaledb` and the four tables exist.

---

# Stage 1 — Digital twin (primary data source) · owner M3

### Step 3 — Section topology · M3 · stage 1
**Files:** [network.py](../data/simulator/cascadeguard_sim/network.py), [section.example.yaml](../data/simulator/config/section.example.yaml)
**← After:** infra is up (nothing else needed; this is the root of the data track).
**→ Before:** the engine (Step 5) moves trains over this; the graph (Step 12) is built from it.
**Do:** load stations/block-sections/platforms/headways from the YAML into `SectionNetwork`.
**Verify:** `SectionNetwork.from_yaml(...)` returns the example section's stations & blocks.

### Step 4 — Timetable + rake links · M3 · stage 1
**Files:** [timetable.py](../data/simulator/cascadeguard_sim/timetable.py)
**← After:** the network (services run on its blocks).
**→ Before:** the engine schedules services on this; the graph's **rake-link** edges (Step 12) come from here.
**Do:** parse services, scheduled arr/dep, and `RakeLink` (inbound→outbound turnarounds).
**Verify:** `Timetable.from_yaml(...)` lists services and at least one rake link.

### Step 5 — SimPy engine emitting events · M3 · stage 1
**Files:** [engine.py](../data/simulator/cascadeguard_sim/engine.py)
**← After:** network + timetable (the substrate and the schedule).
**→ Before:** ingestion (Step 7) consumes these `TrainEvent`s; they must match `events.schema.json`.
**Do:** discrete-event loop advancing trains over blocks under headway/platform constraints,
yielding events with **event-time**.
**Verify:** `run(horizon_min=120)` yields a stream of schema-valid events for the example section.
**🎯 Checkpoint:** you now have a live, deterministic data source — the rest of the system has fuel.

### Step 6 — Scenarios + calibration · M3 · stage 1
**Files:** [scenarios.py](../data/simulator/cascadeguard_sim/scenarios.py), [calibration.py](../data/simulator/cascadeguard_sim/calibration.py)
**← After:** the engine (you inject into a running sim).
**→ Before:** ML (Stage 4) trains on rare-event scenarios; the demo replays a calibrated cascade.
**Do:** implement disruption injectors (fog regime, OHE failure, freight conflict, derailment)
and fit baseline running to a historical dump.
**Verify:** injecting `ohe_failure` produces a visible downstream delay bloom in the event stream.

---

# Stage 2 — Ingestion & validation · owner M3

### Step 7 — Twin adapter · M3 · stage 2
**Files:** [twin_adapter.py](../data/ingestion/cascadeguard_ingest/adapters/twin_adapter.py)
**← After:** the engine's event stream (Step 5).
**→ Before:** the buffer (Step 8) persists whatever this normalizes.
**Do:** wrap the engine and emit normalized, schema-conformant event dicts.
**Verify:** the adapter yields the same events as the engine, contract-validated.

### Step 8 — Store-and-forward buffer · M3 · stage 2
**Files:** [store_forward.py](../data/ingestion/cascadeguard_ingest/buffer/store_forward.py)
**← After:** the twin adapter (Step 7) and Redis (Step 2).
**→ Before:** the validation gate (Step 9) and the worker (Step 25) consume from this stream.
**Do:** append events to a Redis Stream with event-time + watermark; consumer-group read with replay.
**Verify:** events survive a consumer restart (replayed, not lost).

### Step 9 — Validation / anomaly gate · M3 · stage 2
**Files:** [anomaly_gate.py](../data/ingestion/cascadeguard_ingest/validation/anomaly_gate.py), [map_matching.py](../data/ingestion/cascadeguard_ingest/validation/map_matching.py)
**← After:** buffered events (Step 8).
**→ Before:** the graph/ML (Stages 3–4) must only ever see clean events.
**Do:** schema + de-dup + monotonic event-time + `Δpos ≤ vmax·Δt`; map-match GPS + Kalman smooth;
quarantine to a dead-letter instead of crashing.
**Verify:** a hand-crafted teleporting fix is quarantined; a valid one passes.

### Step 10 — Alternate adapters · M3 · stage 2
**Files:** [coa_rtis_adapter.py](../data/ingestion/cascadeguard_ingest/adapters/coa_rtis_adapter.py), [ntes_scrape.py](../data/ingestion/cascadeguard_ingest/adapters/ntes_scrape.py), [circuit_breaker.py](../data/ingestion/cascadeguard_ingest/circuit_breaker.py), [weather_tsr.py](../data/ingestion/cascadeguard_ingest/adapters/weather_tsr.py)
**← After:** the twin-adapter pattern (Step 7) — these mirror its interface.
**→ Before:** the graph/ML read a `regime` feature from weather; the prod path is demo-ready but optional.
**Do:** mock COA/RTIS replay; NTES scrape behind the breaker (off by default); weather→regime label.
**Verify:** flipping `CG_DATA_SOURCE` swaps adapters without touching downstream; breaker trips on errors.

---

# Stage 3 — Heterogeneous dependency graph · owner M2

### Step 11 — Graph schema · M2 · stage 3
**Files:** [schema.py](../data/graph/cascadeguard_graph/schema.py)
**← After:** the timetable (Step 4) defines what edges exist.
**→ Before:** the builder (Step 12) and the GNN's relational layers (Step 15) key off these types.
**Do:** finalize node/edge types `{block, platform, rake-link, crew, loco}` and feature names.
**Verify:** the `EdgeType` enum and feature lists match what the model will expect.

### Step 12 — Build the hetero graph · M2 · stage 3
**Files:** [builder.py](../data/graph/cascadeguard_graph/builder.py)
**← After:** network + timetable (Steps 3–4) and the schema (Step 11).
**→ Before:** ML inference (Step 18) pulls `k_hop_subgraph`s from here.
**Do:** assemble a `HeteroData` graph with typed edges (rake-link from the timetable) and
learned-weight placeholders; implement event-scoped `k_hop_subgraph`.
**Verify:** a disruption node returns a sane k-hop subgraph with all edge types present.

### Step 13 — Graph store + rebuild · M2 · stage 3
**Files:** [store.py](../data/graph/cascadeguard_graph/store.py), [rebuild.py](../data/graph/cascadeguard_graph/rebuild.py)
**← After:** a built graph (Step 12).
**→ Before:** inference uses the sparse hot path; drift monitoring (Step 18) triggers rebuilds.
**Do:** PyG sparse adjacency for inference + GraphML/GeoJSON export; timetable-diff rebuild.
**Verify:** export round-trips; a timetable change triggers a rebuild.

---

# Stage 4 — ML prediction core · owners M1 (+M2)

### Step 14 — Data module · M2 · stage 4
**Files:** [data_module.py](../ml/cascadeguard_ml/training/data_module.py)
**← After:** clean events (Stage 2) + the graph (Stage 3) + scenarios (Step 6).
**→ Before:** training (Step 16) and inference (Step 18) consume these windows.
**Do:** assemble delay-sequence windows paired with the subgraph; mix in simulator rare events.
**Verify:** one batch yields aligned (history, subgraph, target) tensors.

### Step 15 — The ST-GNN · M1 · stage 4
**Files:** [layers.py](../ml/cascadeguard_ml/models/layers.py), [hetero.py](../ml/cascadeguard_ml/models/hetero.py), [stgnn.py](../ml/cascadeguard_ml/models/stgnn.py)
**← After:** the graph schema (Step 11) and data module (Step 14).
**→ Before:** training (Step 16) fits it; inference (Step 18) runs it.
**Do:** Graph WaveNet/DCRNN over the hetero encoder; output per-node risk + delay distribution.
**Verify:** a forward pass on one batch returns `NodePrediction`s of the right shape.

### Step 16 — Train + tail-aware loss · M1 · stage 4
**Files:** [losses.py](../ml/cascadeguard_ml/training/losses.py), [train.py](../ml/cascadeguard_ml/training/train.py), [stgnn.example.yaml](../ml/configs/stgnn.example.yaml)
**← After:** model + data module (Steps 14–15).
**→ Before:** inference (Step 18) loads the checkpoint this writes.
**Do:** focal/cost-sensitive loss; training loop writing `ml/checkpoints/stgnn.pt`.
**Verify:** `python -m cascadeguard_ml.training.train --config ...` trains and saves a checkpoint.

### Step 17 — Uncertainty, OOD, explainability · M2 · stage 4
**Files:** [conformal.py](../ml/cascadeguard_ml/uncertainty/conformal.py), [detector.py](../ml/cascadeguard_ml/ood/detector.py), [gnn_explainer.py](../ml/cascadeguard_ml/explain/gnn_explainer.py)
**← After:** a trained model (Step 16).
**→ Before:** inference (Step 18) attaches intervals + a "why"; OOD triggers the twin fallback.
**Do:** conformal calibrator → intervals; Mahalanobis OOD flag; GNNExplainer one-liner.
**Verify:** a prediction comes back with a coverage-checked interval and a readable attribution.

### Step 18 — Inference + eval · M1+M2 · stage 4
**Files:** [inference.py](../ml/cascadeguard_ml/inference.py), [calibration.py](../ml/cascadeguard_ml/eval/calibration.py), [ablation.py](../ml/cascadeguard_ml/eval/ablation.py)
**← After:** everything in Stage 4 + the graph store (Step 13).
**→ Before:** the reroute engine (Stage 5) and the worker (Step 25) call inference; the ablation is your proof slide.
**Do:** `predict_from_station()` composing model+conformal+explainer+OOD; reliability curve; rake-link ablation.
**Verify:** `python -m cascadeguard_ml.inference --station PNBE` prints the cascade vector; ablation shows topology edges lift tail recall.
**🎯 Checkpoint:** prediction works end-to-end on the twin — the moat is real and measurable.

---

# Stage 5 — Re-routing (the core output) · owner M5

### Step 19 — Alternative-train query · M5 · stage 5
**Files:** [routing.py](../services/reroute-engine/cascadeguard_reroute/routing.py)
**← After:** the timetable/graph (you enumerate real alternatives).
**→ Before:** ticketing (Step 20) and the allocator (Step 21) refine these candidates.
**Do:** top-k candidate trains from origin→dest after a time.
**Verify:** a disrupted journey returns plausible alternatives.

### Step 20 — Ticketing reality · M5 · stage 5
**Files:** [ticketing.py](../services/reroute-engine/cascadeguard_reroute/ticketing.py)
**← After:** candidates (Step 19).
**→ Before:** the allocator (Step 21) needs validity + live availability to avoid full trains.
**Do:** model reserved-ticket validity + WL/Tatkal/availability (IRCTC mocked, clearly labelled).
**Verify:** a reserved ticket is correctly flagged as not valid on an arbitrary alternative.

### Step 21 — Capacity-aware allocation + feedback · M5 · stage 5
**Files:** [allocator.py](../services/reroute-engine/cascadeguard_reroute/allocator.py), [feedback.py](../services/reroute-engine/cascadeguard_reroute/feedback.py)
**← After:** routing + ticketing (Steps 19–20).
**→ Before:** the worker (Step 25) and the API `/reroute` (Step 26) call this.
**Do:** capacity-constrained/fractional allocation (no herding); accepted re-routes feed back as demand.
**Verify:** two passengers, same disruption → **different, capacity-feasible** routes.

---

# Stage 6 — Decisioning & messaging · owner M5

### Step 22 — Cost-sensitive trigger · M5 · stage 6
**Files:** [trigger.py](../services/notifier/cascadeguard_notify/trigger.py)
**← After:** predictions + conformal intervals (Stage 4).
**→ Before:** the worker (Step 25) asks "should I alert?" here, not at a magic 65%.
**Do:** notify when expected passenger-minutes saved > expected false-alarm cost, using the interval.
**Verify:** a low-confidence small delay does not fire; a confident large cascade does.

### Step 23 — LLM phrasing (template-first, async) · M5 · stage 6
**Files:** [client.py](../services/llm-agent/cascadeguard_llm/client.py), [prompts.py](../services/llm-agent/cascadeguard_llm/prompts.py), [phrasing.py](../services/llm-agent/cascadeguard_llm/phrasing.py), [en.delay-bands.txt](../services/llm-agent/cascadeguard_llm/templates/en.delay-bands.txt)
**← After:** reroute options (Stage 5) to phrase.
**→ Before:** the worker (Step 25) emits a template alert instantly, then enriches via this.
**Do:** instant deterministic template; async Claude enrichment that falls back on failure;
safety fields stay templated.
**Verify:** with the network off, you still get a correct templated alert; with it on, prose improves.

### Step 24 — FCM delivery · M5 · stage 6
**Files:** [fcm.py](../services/notifier/cascadeguard_notify/fcm.py)
**← After:** a phrased alert (Step 23).
**→ Before:** the app (Step 27) receives these pushes.
**Do:** FCM send (works app-closed); never block delivery on the LLM.
**Verify:** a test token receives a push.

---

# Stage 7 — Orchestration & serving · owner M5

### Step 25 — The worker pipeline · M5 · stage 7
**Files:** [pipeline.py](../services/worker/cascadeguard_worker/pipeline.py), [degradation.py](../services/worker/cascadeguard_worker/degradation.py)
**← After:** **everything in Stages 2–6** — this is where they connect.
**→ Before:** the API (Step 26) and frontends read the predictions/alerts this produces.
**Do:** consume buffer → k-hop subgraph → inference → trigger → reroute → template alert (+async LLM) → push/persist;
degradation ladder + staleness watermark.
**Verify:** a twin-injected delay flows all the way to a push, all on the twin.
**🎯 Checkpoint:** the whole backend works headless end-to-end.

### Step 26 — The API · M5 · stage 7
**Files:** [config.py](../services/api/cascadeguard_api/config.py), [deps.py](../services/api/cascadeguard_api/deps.py), [routers cascade/stations/corridor/reroute/ws](../services/api/cascadeguard_api/routers/), [main.py](../services/api/cascadeguard_api/main.py)
**← After:** the worker writes predictions/cases (Step 25).
**→ Before:** both frontends (Stage 8) consume REST + WS.
**Do:** read endpoints + the Corridor Risk API + a WS that pushes deltas; responses carry the staleness watermark.
**Verify:** `GET /cascade/{train}` returns live risk; `/docs` lists the endpoints; WS streams deltas.

---

# Stage 8 — Frontend · owner M4

### Step 27 — Passenger app (Expo / React Native, primary) · M4 · stage 8
**Files:** [_layout.tsx](../frontend/passenger-app/app/_layout.tsx), [index.tsx](../frontend/passenger-app/app/index.tsx), [RerouteCard.tsx](../frontend/passenger-app/components/RerouteCard.tsx), [push.ts](../frontend/passenger-app/lib/push.ts), [api.ts](../frontend/passenger-app/lib/api.ts), [app.json](../frontend/passenger-app/app.json)
**← After:** the API + push (Steps 24, 26).
**→ Before:** the demo's "saved before the announcement" moment (Stage 10).
**Do:** Expo Router tabs; PNR registration; the re-route card (risk, interval, feasible alternatives, seats, why, data-age); `expo-notifications` registration + handling.
**Verify:** `npx expo start`, run in Expo Go; a worker-driven cascade lands as a background push *before* the simulated announcement.
**🎯 Checkpoint:** the headline demo works on a real phone.

### Step 28 — Operator dashboard (context) · M4 · stage 8
**Files:** [main.tsx](../frontend/operator-dashboard/src/main.tsx), [RiskHeatmap.tsx](../frontend/operator-dashboard/src/components/RiskHeatmap.tsx), [CascadeChain.tsx](../frontend/operator-dashboard/src/components/CascadeChain.tsx), [StationDrilldown.tsx](../frontend/operator-dashboard/src/components/StationDrilldown.tsx), [ws.ts](../frontend/operator-dashboard/src/lib/ws.ts)
**← After:** the API WS (Step 26).
**→ Before:** the demo's "watch the cascade light up" beat.
**Do:** Mapbox heatmap + cascade chain (with the per-hop why) + station drill-down, fed by WS deltas.
**Verify:** an injected delay turns downstream nodes amber/red live.

---

# Stage 9 — Helpline & grievance subsystem · owners M5 (service) + M4 (screens)
*Parallel track — needs only contracts (Step 1) + DB (Step 2).*

### Step 29 — Speech + understanding · M5 · stage 9
**Files:** [asr.py](../services/helpline/cascadeguard_helpline/asr.py), [tts.py](../services/helpline/cascadeguard_helpline/tts.py), [intent.py](../services/helpline/cascadeguard_helpline/intent.py), [passenger.py](../services/helpline/cascadeguard_helpline/passenger.py)
**← After:** the DB + contracts.
**→ Before:** the agent (Step 31) chains these.
**Do:** Bhashini/Whisper ASR + NMT (mocked); intent+entity extraction; PNR/profile lookup.
**Verify:** a Hindi audio clip → transcript → category + extracted PNR.

### Step 30 — Routing, cases, dispatch · M5 · stage 9
**Files:** [authorities.py](../services/helpline/cascadeguard_helpline/authorities.py), [authority_router.py](../services/helpline/cascadeguard_helpline/authority_router.py), [cases.py](../services/helpline/cascadeguard_helpline/cases.py), [dispatch.py](../services/helpline/cascadeguard_helpline/dispatch.py), [authorities.example.yaml](../services/helpline/cascadeguard_helpline/config/authorities.example.yaml)
**← After:** understanding (Step 29).
**→ Before:** the agent (Step 31) opens + dispatches cases through these.
**Do:** category→department routing (low-confidence→helpdesk); case lifecycle persisted to `grievance_cases`; RailMadad/email dispatch (mocked).
**Verify:** a "security" grievance routes to RPF and persists a case with status `open`.

### Step 31 — The helpline agent · M5 · stage 9
**Files:** [agent.py](../services/helpline/cascadeguard_helpline/agent.py)
**← After:** all helpline modules (Steps 29–30).
**→ Before:** the API routers (Step 32) call this per turn.
**Do:** orchestrate transcribe→understand→fetch→open case→route→dispatch→reply (text + optional TTS).
**Verify:** one `handle()` call turns an utterance into a routed, tracked case + a reply.

### Step 32 — Helpline API routers · M5 · stage 9
**Files:** [helpline.py](../services/api/cascadeguard_api/routers/helpline.py), [queries.py](../services/api/cascadeguard_api/routers/queries.py) *(already wired in [main.py](../services/api/cascadeguard_api/main.py))*
**← After:** the agent + cases (Steps 31, 30).
**→ Before:** the app screens (Step 33) call these.
**Do:** `POST /helpline/chat` (text/audio) → agent; `GET /queries[/{id}]` → case list + history.
**Verify:** posting a message returns a case id + authority; `GET /queries` lists it with status.

### Step 33 — Helpline + My-Queries screens · M4 · stage 9
**Files:** [speech.ts](../frontend/passenger-app/lib/speech.ts), [HelplineChat.tsx](../frontend/passenger-app/components/HelplineChat.tsx), [QueryHistory.tsx](../frontend/passenger-app/components/QueryHistory.tsx), [helpline.tsx](../frontend/passenger-app/app/helpline.tsx), [queries.tsx](../frontend/passenger-app/app/queries.tsx)
**← After:** the helpline API (Step 32).
**→ Before:** the demo's support beat.
**Do:** chat UI (text + mic via `speech.ts`); My-Queries list with status badges + history drill-down.
**Verify:** a spoken complaint opens a case that then appears under My Queries with a live status.
**🎯 Checkpoint:** the full app (info + re-route + helpline + history) works.

---

# Stage 10 — Integration, demo, honesty · owners all

### Step 34 — End-to-end tests · all · stage 10
**Files:** [tests/e2e/](../tests/e2e/) (add test modules)
**← After:** the full vertical slice (Stages 7–9).
**→ Before:** demo confidence — these are the scenarios you'll show.
**Do:** replay-a-cascade, two-passenger-different-reroute, kill-the-feed-degrades, teleporting-GPS-quarantined,
spoken-grievance-routes-correctly.
**Verify:** all five pass on the twin with no live network.

### Step 35 — Demo scripts + honesty doc · all · stage 10
**Files:** [setup.sh](../infra/scripts/setup.sh), [run_demo.sh](../infra/scripts/run_demo.sh), `WHAT_WE_BUILT.md` (new)
**← After:** passing tests (Step 34).
**→ Before:** the pitch.
**Do:** one-command setup + demo replay; `WHAT_WE_BUILT.md` (real/mocked/next); rehearse the 4-min arc +
the ablation slide; practice killing the feed live.
**Verify:** cold `run_demo.sh` < 4:00, zero live-network dependency, survives the three killer questions
([problem-statement.md §12](problem-statement.md)).

---

## Definition of done (ties to the submission checklist)
- Twin replays a real historical cascade; demo runs with the cable unplugged.
- ST-GNN + rake-link ablation shows topology lifts tail recall; reliability curve shown.
- Two passengers → different feasible re-routes; alert fires before the simulated announcement.
- Helpline: spoken regional-language complaint → routed case → visible status in My Queries.
- Graceful degradation demonstrated live; `WHAT_WE_BUILT.md` declares real/mocked/next.
