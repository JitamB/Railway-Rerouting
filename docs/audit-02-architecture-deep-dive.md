# Audit 02 — Architectural & Process Deep-Dive

> Critical evaluation of the proposed workflow and architecture: bottlenecks, single points of failure (SPOFs), latency, and naive assumptions about railway data, real-time processing, hardware, and edge.

The architecture is *plausible-looking* — which is the trap. It reads like a clean reference diagram, but several boxes hide the actual hard problems, and two of the claims are internally contradictory. Below, per layer.

---

## 1. Single Points of Failure & Bottlenecks

### 1.1 The data ingestion layer is one giant SPOF
Everything downstream — GNN, LSTM, dashboard, passenger push, API — is fed by **one source: NTES**. If NTES is unreachable, rate-limits you, changes its DOM, or returns stale/garbage data, **the entire system goes blind**. There is no redundancy, no fallback feed, no graceful degradation described.

- **Severity: critical.** This is the classic "single upstream dependency" failure and it's the most likely thing to break live.
- **Fix:** (a) Primary = your own simulator/digital twin (deterministic, always available — see `audit-03 §3`). (b) Treat live NTES as an *optional enrichment*, not a dependency. (c) Add a **store-and-forward buffer** (the Kafka/Redis layer is well-placed for this) + **schedule-based prior** so that when the feed dies, the system falls back to timetable expectations and dead-reckoning from last-known position/speed instead of going dark.

### 1.2 In-memory NetworkX graph won't scale and isn't HA
The tech stack lists **"NetworkX (in-memory) + GraphML export"** for graph storage. For a single-zone prototype this is fine. As a claimed path to **all 18 zones** (Roadmap Phase 2) it falls over:

- IR scale: **~7,300+ stations, ~13,000+ daily passenger trains, ~68,000 route-km, 9,000+ freight.** A full-network conflict/dependency graph with temporal edges is large and mutates every timetable revision.
- NetworkX is single-process, single-threaded Python objects — **no concurrency, no persistence, no HA**. A crash loses graph state; recomputing cascade queries network-wide every 60s in pure Python is slow.
- **Fix:** Compile the hot path. Options: (a) **PyG `HeteroData` + precompiled sparse adjacency** for inference; (b) a real graph store if you need persistence/queries (Neo4j or, lighter, **Memgraph**/`igraph`); (c) **localize computation** — you almost never need the whole network, only the *k*-hop subgraph around the disrupted node. Incremental, event-scoped subgraph inference instead of global recompute.

### 1.3 Two separate models = a consistency SPOF
GNN (cascade across stations) and LSTM (per-corridor time-series) are **independent models that will disagree.** The GNN says Varanasi is 54% at-risk; the LSTM says the specific train arrives roughly on time. Which does the operator believe? Which drives the passenger push? Nothing in the doc reconciles them.

- **Severity: medium-high** — disagreement is guaranteed (different inductive biases, different training objectives) and undermines trust the moment a juror notices.
- **Fix:** Collapse to **one spatio-temporal graph model** (DCRNN / Graph WaveNet / Temporal Graph Network) that does space *and* time jointly. One coherent output, no reconciliation problem. Detail in `audit-03 §1`.

### 1.4 LLM in the critical path is a latency + availability SPOF
The Claude API call is "only when threshold crossed" — good instinct — but it's still **a synchronous network round-trip on the path to the passenger alert**, and it **breaks the offline/edge claim** (§3 below). If the venue network is flaky (it will be), pushes stall.

- **Fix:** Make the LLM **fully asynchronous and non-blocking**: emit the alert from a **deterministic template** instantly, then *optionally* enrich with LLM phrasing when/if the call returns. Pre-generate templated guidance per (delay-band × language) so the system degrades to a still-useful canned message offline. Never let the alert wait on the LLM.

### 1.5 WebSocket fan-out and 60s recompute cadence
"Updated every 60 seconds" network-wide, pushed over WebSocket to dashboards: fine for one zone/one demo, but the recompute is global and synchronous. Bottleneck appears the moment you add zones or clients.
- **Fix:** Event-driven recompute (only recompute subgraphs touched by a new delay event), not a global 60s tick. Debounce/coalesce events. Push deltas, not full state.

---

## 2. Latency budget — the numbers don't reconcile

The doc claims a **20–40 minute passenger decision window** but builds on a **2-minute NTES poll** of a feed already lagged ~2–5 min. End-to-end:

```
event occurs
  └─► NTES public lag         ~2–5 min   (you cannot remove this)
       └─► your poll          0–2 min
            └─► cascade matures to cross 65%   variable, often +mins
                 └─► inference (ms) + LLM RTT (~1–3 s, if network OK)
                      └─► FCM delivery + user reaction + rebooking   minutes
```

The *informational* latency floor is **~4–10 minutes before you can even fire**, dominated by the public-feed lag you don't control. The 20–40 min window only exists on the **RTIS 30-sec feed** (which you can't access) **and** for cascades that telegraph far in advance. **Action:** state the window honestly — single-digit minutes on public data; 20–40 min only once integrated with COA/RTIS — and frame the passenger value as *"earlier than the official delay announcement"* rather than a fixed minute count you can be caught on. (See `audit-01 §4`.)

---

## 3. Naive assumptions — itemized

### 3.1 "NTES Live API … every 2 minutes" — **the feed doesn't exist as an API**
Covered fully in `audit-01 §3`. In architecture terms: you've drawn a clean arrow from a box that isn't a real interface. Replace the box with **(primary) Digital-Twin Simulator** + **(production-path) COA/RTIS adapter (mocked)** + **(optional) NTES scrape with circuit-breaker**.

### 3.2 The "station dependency graph" models the wrong physics
The doc's edges are **station-to-station** ("delay at A propagates to B"). But cascade in railways is not primarily a station-adjacency phenomenon — it's driven by:

- **Block-section / track occupancy conflicts** (two trains can't occupy the same block; this is where precedence is decided).
- **Platform occupancy** (a train holds a platform, the next can't berth) — partially captured.
- **Rake links** — the *same physical trainset* turns around to become a later service. If the inbound is late, the outbound *starts* late, regardless of topology. **This is a top cascade source and the doc misses it entirely.**
- **Crew/loco links** — crew duty hours (HOER limits) and locomotive availability propagate delay across otherwise-unrelated trains.

A station-adjacency graph will systematically mispredict because it's modelling the wrong dependency. **Fix:** Make it a **heterogeneous, multi-relational graph** with edge types `{block-conflict, platform-conflict, rake-link, crew-link, loco-link}` and **learn** the propagation coefficients from data (don't hand-set them — see §3.4).

### 3.3 GraphSAGE on a static 2-hop neighbourhood ignores time and direction
- **GraphSAGE is inductive (good)** but it's a **static** aggregator. Cascade propagation is **temporal and directional** — delay flows forward in time along the schedule. A static 2-hop message-pass captures neither the time-ordering nor the fact that a 2-hop cascade can take 90 minutes to mature (the doc's own demo says so).
- **2-hop is too shallow** for the 6-station, 90-minute spread the demo advertises — that's easily 4–6 hops.
- **Fix:** Temporal/spatio-temporal GNN (DCRNN, Graph WaveNet, **TGN** for event streams). If you want to keep a propagation-process flavour, a **graph-conditioned Hawkes / point process** literally models "an event at A raises the intensity of events at downstream nodes" — which *is* a cascade. That framing alone is a wow slide.

### 3.4 Hand-built propagation coefficients = circular / unfalsifiable
"Edge encodes historical propagation coefficient W" — if W is hand-tuned from "schedules and historical patterns" rather than **learned end-to-end with the GNN**, the model is partly hand-engineered and a juror will ask "did you fit these or guess them?" **Fix:** learn edge weights as attention/parameters jointly with the prediction objective; report an ablation (learned vs heuristic W) to prove they matter.

### 3.5 "Edge-quantised, runs on a Raspberry Pi, no cloud needed" — contradicts the data model
This is the most important architectural contradiction in the document:

- A **cascade is a network-level computation.** To predict propagation from A through B, C, D you need the **live state of B, C, D and the graph** — i.e., you need network-wide data *at the node doing inference*.
- A lone Raspberry Pi at a junction **cannot compute network cascades** without receiving that network state from somewhere — which means it **needs connectivity**, which contradicts "no cloud / offline."
- INT8 quantised inference on a Pi is fine for *running the model*; it does nothing to solve *getting the inputs*. The doc conflates **model portability** with **data availability**.
- **Fix / honest framing:** Edge nodes do **local sensing + local single-node inference** (e.g., "is my platform about to conflict?") and **forward features upstream**; the **network cascade is computed centrally** (or at a zonal aggregator) and pushed back down. Say *that* — it's a real edge/fog architecture (sense at edge, reason in the middle), not "the whole brain on a Pi." Also: the Claude API call is **cloud-dependent by definition**, so "offline-capable" and "Claude in the pipeline" cannot both be headline claims. Reconcile them (template-first, LLM-optional).

### 3.6 Kafka "local" for a single-zone demo is architecture theatre
Kafka is justifiable for genuine high-throughput event streaming, but for a single-zone hackathon prototype it's often **complexity for the slide, not the system** — and it's a fragile thing to bring up live (ZooKeeper/KRaft, topic config). If you're truly doing event-sourced delay events, keep it and *show* it. If not, **Redis Streams** gives you 90% of the value with 10% of the operational risk during a live demo. Don't run Kafka just to draw the box. (Per project `CLAUDE.md`: no flexibility/infra that wasn't requested.)

### 3.7 Weather as an "hourly, free-tier 1000 calls/day" feature is under-modelled
- Weather's real effect on rail is via **caution orders / Temporary Speed Restrictions (TSRs)** (fog → 60 kmph + detonators; monsoon → patrolling, speed cuts; heat → buckling). These are **step-change regime shifts**, not a smooth "severity score."
- 1,000 calls/day across a multi-station route at hourly cadence is tight and **single-keyed = another SPOF / rate-limit risk.**
- **Fix:** Model weather as a **regime variable** that switches the model's operating point (normal vs degraded), and ingest **actual caution-order/TSR signals** where available rather than inferring everything from a weather API.

### 3.8 "5+ years of historical NTES data" — acquisition is itself unsolved
You assert the training corpus but not how you obtain 5 years of fine-grained running data when there's no API. Kaggle dumps exist but are **partial, noisy, and dated.** Don't assume the corpus; **state your actual source and its limits**, and lean on the **simulator** to generate labelled cascade scenarios you can't get from real logs (rare events especially — see `audit-04 §2,§6`).

---

## 4. Process / workflow gaps

- **No feedback loop on prediction quality.** Nothing logs predicted-vs-actual to detect drift or recalibrate. Add an online scoring loop (Brier score / calibration) — also great for the demo ("our model is calibrated, here's the reliability curve").
- **No confidence/feedback affordance for the passenger.** A proactive alert that turns out wrong erodes trust fast. Surface the *why* + confidence with every push, and let users mark "this helped / didn't" to close a quality loop. (If you later add the optional operator layer in `audit-03 §7`, it needs an **action → recommend → accept/reject → log** workflow — but that's off the critical path for the passenger-focused build.)
- **Threshold (65%) is a magic number.** A fixed global threshold ignores that the *cost* of a missed cascade varies by train/section. Replace with a **cost-sensitive / utility-based trigger** (expected delay-minutes saved > expected cost of false alarm).
- **No data-validation gate** between ingestion and models. NTES emits teleporting/stale/zeroed positions; feeding those straight to the GNN produces phantom cascades. Add a validation/anomaly stage (see `audit-04 §3, §8`).

---

## 5. What the architecture should look like after hardening

```
┌─────────────────────────────────────────────────────────────────┐
│ DATA LAYER                                                        │
│  PRIMARY: Digital-Twin Simulator (discrete-event, always-on)      │
│  PROD-PATH: COA/RTIS adapter (mocked; the real integration point) │
│  OPTIONAL: NTES scrape behind a circuit-breaker  + Weather/TSR    │
└───────────────┬───────────────────────────────────────────────────┘
                ▼   [validation + anomaly gate]   [store-and-forward buffer]
┌─────────────────────────────────────────────────────────────────┐
│ PREDICT: one Spatio-Temporal GNN over a HETERO graph              │
│   edges: block-conflict | platform | rake-link | crew | loco      │
│   output: per-node cascade risk + delay dist. + conformal interval│
└───────────────┬───────────────────────────────────────────────────┘
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ RE-ROUTE (CORE): capacity-aware, congestion-safe allocation       │
│   inputs: cascade risk + live availability/ticket validity        │
│   → per-passenger feasible alternatives (no herding)              │
│   → push template-first, LLM-async, with a one-line "why"         │
└───────────────┬───────────────────────────────────────────────────┘
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ SERVE: Passenger PWA (primary) | Operator heatmap (context)       │
│        REST/WS live feed                                          │
│  · · · OPTIONAL Phase-2: CP-SAT/RL operator decision layer · · ·  │
└─────────────────────────────────────────────────────────────────┘
```

The shape barely changes; the **emphasis** changes — a real data source on top, one model instead of two, and a hardened capacity-aware re-router as the core output. The operator decision layer is an optional Phase-2 expansion (`audit-03 §7`), not part of the critical path. That's the architecture that survives the deep-dive.
