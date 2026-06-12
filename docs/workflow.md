# CascadeGuard — Workflow

Two workflows in one file:
- **Part A — Runtime pipelines:** how the *running* system works, step by step —
  **A.1** cascade prediction → re-routing, and **A.2** the helpline / grievance flow.
- **Part B — Build sequence:** how the 5-person team *builds* it, phase by phase.

Read [problem-statement.md](problem-statement.md) first for the architecture and the
hardening decisions these workflows implement.

---

## Part A.1 — Cascade pipeline (event → passenger push)

Each numbered stage maps to a directory in the scaffold; the audit reference is the risk it
closes.

```
 (1) source ─► (2) buffer+watermark ─► (3) validation gate ─► (4) k-hop subgraph
                                                                       │
 (9) degrade ◄─ (8) serve/push ◄─ (7) re-route ◄─ (6) trigger ◄─ (5) ST-GNN infer
```

1. **Emit event** — a train-position / delay event enters the system.
   - Primary: **digital twin** (`data/simulator/`).
   - Production: **COA/RTIS adapter** (`data/ingestion/adapters/coa_rtis_adapter.py`, mocked).
   - Optional: **NTES scrape** behind a circuit-breaker (`adapters/ntes_scrape.py`).
   - Context: **weather/TSR** as a regime signal (`adapters/weather_tsr.py`).

2. **Buffer + stamp** — write to a **Redis Streams** store-and-forward buffer
   (`data/ingestion/buffer/store_forward.py`); attach **event-time + watermark** so "current
   delay" is computed from when the train was actually there, not when we heard about it.
   *(audit-04 §9)*

3. **Validate / anomaly-gate** (`data/ingestion/validation/`):
   - schema check, de-duplication, monotonic event-time ordering;
   - physical-plausibility (`Δposition ≤ vmax · Δt`);
   - **map-matching + Kalman** smoothing to snap GPS to the track graph and reject teleports;
   - suspect records → **dead-letter quarantine** (never crash the live graph). *(audit-04 §3, §8)*

4. **Build the working subgraph** — fetch the **k-hop subgraph** around the disrupted node
   from the heterogeneous dependency graph (`data/graph/`), not the whole network. Edge
   types `{block, platform, rake-link, crew, loco}`. *(audit-02 §1.5, audit-04 §10)*

5. **Predict** — run the **one spatio-temporal GNN** (`ml/cascadeguard_ml/inference.py`):
   - per-node **cascade risk** + **delay distribution** + **conformal interval**;
   - **OOD check** (`ml/.../ood/detector.py`) → if off-distribution, fall back to the
     **simulator** to project propagation from first principles + widen intervals;
   - attach a one-line **why** via GNNExplainer/attention. *(audit-03 §1/§4/§5, audit-04 §2)*

6. **Trigger decision** — a **cost-sensitive** trigger (`services/notifier/.../trigger.py`):
   notify when *expected passenger-minutes saved > expected false-alarm cost*, **not** a
   magic 65% threshold. *(audit-02 §4)*

7. **Re-route (core)** (`services/reroute-engine/`):
   - query deterministic alternatives (`routing.py`);
   - apply **ticket validity / availability** (`ticketing.py`, IRCTC mocked honestly);
   - **capacity-aware fractional allocation** (`allocator.py`) so two passengers with the
     same disruption get **different, feasible** routes — no herding;
   - feed accepted re-routes back as demand (`feedback.py`). *(audit-01 §5, audit-03 §3, audit-04 §7)*

8. **Serve / push**:
   - emit a **template-first** alert instantly (safety-critical fields — train no., platform,
     time — are templated, never LLM-generated);
   - **asynchronously** enrich phrasing via Claude (`services/llm-agent/`) when reachable;
   - deliver to the **passenger app** via push (`services/notifier/fcm.py` → expo-notifications, FCM/APNs) and update the
     **operator heatmap** over WebSocket (`services/api/routers/ws.py`). *(audit-02 §1.4, §3.5)*

9. **Degrade gracefully** (`services/worker/degradation.py`) — if the feed drops:
   live → **dead-reckoning** (propagate along schedule at last-known speed) → **schedule-only
   prior**. Every prediction carries a **staleness watermark**; the UI greys out past a
   bound. Never go blank, never lie. *(audit-04 §1)*

The **worker** (`services/worker/pipeline.py`) orchestrates stages 2→8; the **API**
(`services/api/`) serves reads and the WebSocket feed.

---

## Part A.2 — Helpline / grievance flow (query → routed case → status)

A passenger-initiated, request/response flow (not event-driven). Backed by
`services/helpline/`, exposed via `services/api` routers `helpline` + `queries`.

```
 passenger asks (text | speech)
   └─►(1) POST /helpline/chat
        └─►(2) ASR + translate ─►(3) understand ─►(4) fetch details ─►(5) open case
                                                                            │
   passenger sees status ◄─(8) My Queries ◄─(7) dispatch ◄─(6) route to authority
```

1. **Receive** a turn at `POST /helpline/chat` — text, or a regional-language audio clip
   captured in the app (`lib/speech.ts`, expo-av).
2. **Transcribe + translate** (`helpline/asr.py`) — speech → text via Bhashini/ULCA (Whisper
   fallback); optionally NMT into the agent's working language.
3. **Understand** (`helpline/intent.py`) — LLM agent classifies the grievance category and
   extracts entities (PNR, train, station, coach); low confidence is flagged.
4. **Fetch passenger details** (`helpline/passenger.py`) — resolve PNR/profile to name, train,
   coach, journey (IRCTC mocked honestly); attach only the minimum PII.
5. **Open a tracked case** (`helpline/cases.py`) — persist to `grievance_cases` with status
   `open`; the agent's summary is LLM-phrased, the routing fields are structured.
6. **Route to authority** (`helpline/authority_router.py` + `authorities.py`) — category →
   department from the registry; unsure → general helpdesk, never a guessed department.
7. **Dispatch** (`helpline/dispatch.py`) — forward the structured case to the authority
   (RailMadad/email adapter, mocked); store the external reference for tracking.
8. **Reply + track** — return case id, department, and status to the app (text + optional TTS
   spoken reply). The case appears under **My Queries** (`GET /queries`); status advances
   `open → in_progress → resolved` (or `rejected`) on authority callbacks, with history.

**Privacy:** grievances are PII — minimized, owner-scoped, retention-bounded.

---

## Part B — Team build sequence (phases · owners · verify)

Adapted from the audit's 10-day action plan ([audit-00](audit-00-verdict.md)). Each phase
has a verifiable exit check. Owners reference the roles in
[problem-statement.md §11](problem-statement.md).

### Phase 0 — Scaffold & contracts *(all, day 0)*
- This repository skeleton: directories, manifests, stubs, `docker-compose.yml`,
  `shared/schemas/` event + prediction contracts.
- **verify:** every package imports; `docker compose config` validates; READMEs explain each dir.

### Phase 1 — Kill the data risk *(M3, days 1–2)*
- Discrete-event **digital twin** of one real section (stations, block sections, platforms,
  headways, timetable); calibrate to a static historical NTES dump.
- Ingestion + **validation gate** + Redis Streams buffer; build the **heterogeneous graph** (M2).
- **verify:** the twin replays a real historical cascade; the full demo runs with the network
  cable unplugged.

### Phase 2 — Make the moat real & legible *(M1 + M2, days 3–5)*
- One **spatio-temporal GNN** over the hetero graph; **learn** edge weights.
- **with-vs-without-rake-link ablation**; conformal intervals; reliability curve; OOD detector.
- **verify:** the ablation shows topology edges measurably improve cascade recall; calibration
  curve is shown.

### Phase 3 — Harden re-routing (center of gravity) *(M5, days 6–7)*
- **Capacity-aware** allocation; ticket-validity / availability model (IRCTC mocked);
  cost-sensitive trigger; close the demand loop.
- **verify:** two passengers, same disruption → **different, capacity-feasible** re-routes.

### Phase 4 — Serve it *(M4 + M5, days 6–8, overlaps Phase 3)*
- FastAPI **REST + WebSocket** + Corridor Risk API (`/docs` auto-generated); **template-first
  alerts + async Claude** phrasing; **passenger app** (Expo, push) + **operator heatmap**.
- **verify:** a twin-injected delay produces a phone push *before* the simulated official
  announcement; operator heatmap updates live over WS.

### Phase 4b — Helpline & grievance redressal *(M4 + M5, days 7–9, overlaps Phase 4)*
- `services/helpline/` agent (intent + authority routing + cases + dispatch) behind
  `POST /helpline/chat`; regional-language **ASR** (Bhashini/Whisper, mocked) + optional TTS;
  app **Helpline** chat (text + mic) and **My Queries** status screen; grievance tables.
- **verify:** a spoken Hindi complaint opens a case, routes to the correct department, and
  shows up under My Queries with a status that can advance to *resolved*.

### Phase 5 — Demo weaponization & honesty *(all, days 8–10)*
- Counterfactual + **the one number**; live graceful-degradation demo (kill the feed on
  stage); `WHAT_WE_BUILT.md` (real / mocked / next); rehearse the 4-minute arc.
- **verify:** cold run < 4:00, zero live-network dependency on stage, survives the three
  killer questions ([problem-statement.md §12](problem-statement.md)).

### Phase-2 / roadmap (not a gate)
Operator dispatch optimizer (CP-SAT / Maskable-PPO on Flatland), IoT edge layer
(`iot/`), multi-zone partitioning, multilingual alerts — attempt **only** if Phases 1–5 are
solid; otherwise a roadmap slide. *(audit-03 §7, §8)*
