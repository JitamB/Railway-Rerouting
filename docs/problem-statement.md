# CascadeGuard — Problem Statement (Authoritative)

> Real-Time Delay-Cascade Predictor & Proactive Passenger Re-Routing Engine for Indian Railways.
>
> **One line:** *No consumer app models the network **cascade**, and none re-routes you **before** the railway announces the delay. That's CascadeGuard.*

This is the single source of truth for the project. It consolidates the team's original
vision ([../intuition.md](../intuition.md), "v0") and reconciles it with the five-file
audit ([audit-00](audit-00-verdict.md) … [audit-04](audit-04-flaws-edge-cases.md)). **Where
v0 and the audit disagree, the audit wins** — the verdict's direction is "harden the
passenger-focused concept," and that hardened design is what we build.

---

## 1. Problem

Indian Railways carries ~23 million passengers a day. A single disruption — signal failure,
engine fault, track obstruction, fog regime — rarely stays local. It **propagates**: a late
train holds a platform, blocking the next arrival, which pushes a freight crossing, which
holds a third train. This **cascade** is the silent multiplier behind the network's worst
delay events.

The passenger-facing stack today is **reactive and single-train**. NTES, ixigo, and
Where-is-my-Train tell you *your* train is late *after* the railway confirms it — by which
time the re-routing window has usually closed. None of them:

- models cascade propagation across the **station-dependency topology**;
- issues passenger-specific re-routing **before** the official delay is announced;
- exposes probabilistic downstream risk to operators while the cascade is still maturing.

**The self-authored-PS burden** ([audit-01 §2](audit-01-screening-feasibility.md)): because
we chose this problem, judges grade the *problem* as well as the solution. Our defensible
claim: single-train delay is a solved, saturated problem; **network cascade propagation is
not**, and that is where the multiplied disruption — and the savable passenger-minutes —
actually live.

---

## 2. What CascadeGuard does

Continuously model the dependency graph between stations/platforms/trainsets and answer two
questions in real time:

1. *"If this train is X minutes late now, which downstream stations are at risk, and by how
   much?"* → drives the **operator risk heatmap** (supporting context).
2. *"What is the best **feasible** alternative for Passenger Y right now, in plain
   language?"* → pushed to the **passenger app** (the primary surface) before they know
   there's a problem.

The app also carries a **helpline**: a chatbot that takes **text or regional-language
speech**, understands the query with an **agent**, fetches the passenger's details, opens a
tracked case, and forwards it to the **appropriate authority** (RailMadad-style routing). Every
past query and its status (resolved / pending) is visible under **My Queries**. See §7.5.

**Primacy is explicit:** the passenger app + proactive re-routing is the product; the
operator heatmap is situational-awareness context, not the core. The operator
decision/dispatch optimizer is **Phase-2**, not on the critical path
([audit-00](audit-00-verdict.md), [audit-03 §7](audit-03-worth-winning-upgrades.md)).

---

## 3. Differentiators / the moat

| Dimension | Commodity apps (NTES/ixigo/WiMT) | CascadeGuard |
|---|---|---|
| Unit of prediction | Single-train delay | **Network cascade** over station topology |
| Graph topology | Not modelled | **Heterogeneous dependency graph** (learned, core IP) |
| Timing | Reactive (after confirmation) | **Proactive** (before the official announcement) |
| Passenger role | Passive (you check the app) | Active (system pushes a feasible re-route) |
| Re-routing | None / naive | **Capacity-aware**, ticketing-realistic, no-herding |
| AI role | Prediction = final output | Prediction → re-route → LLM phrasing |

Two genuinely differentiated assets — **GNN-on-topology** and **proactive capacity-aware
re-routing** — must be the first thing a juror sees. Everything else (a dashboard,
single-train prediction) is plumbing and recedes. (See [audit-01 §1](audit-01-screening-feasibility.md).)

---

## 4. Hardened architecture

Superseding the v0 diagram. Source: [audit-02 §5](audit-02-architecture-deep-dive.md).

```
┌─────────────────────────────────────────────────────────────────┐
│ DATA LAYER                                                        │
│  PRIMARY:   Digital-Twin Simulator (discrete-event, always-on)    │
│  PROD-PATH: COA/RTIS adapter (mocked — the real integration point)│
│  OPTIONAL:  NTES scrape behind a circuit-breaker  +  Weather/TSR  │
└───────────────┬───────────────────────────────────────────────────┘
                ▼   [validation + anomaly gate]   [store-and-forward buffer]
┌─────────────────────────────────────────────────────────────────┐
│ PREDICT: ONE Spatio-Temporal GNN over a HETEROGENEOUS graph       │
│   edge types: block-conflict | platform | rake-link | crew | loco │
│   output: per-node cascade risk + delay dist. + conformal interval│
└───────────────┬───────────────────────────────────────────────────┘
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ RE-ROUTE (CORE): capacity-aware, congestion-safe allocation       │
│   inputs: cascade risk + live availability / ticket validity      │
│   → per-passenger feasible alternatives (no herding)              │
│   → push template-first, LLM-async, with a one-line "why"         │
└───────────────┬───────────────────────────────────────────────────┘
                ▼
┌─────────────────────────────────────────────────────────────────┐
│ SERVE: Passenger app (primary) | Operator heatmap (context)       │
│        REST / WebSocket live feed                                 │
│  · · · OPTIONAL Phase-2: CP-SAT / RL operator decision layer · · ·│
└─────────────────────────────────────────────────────────────────┘
```

**Contradictions resolved** ([audit-02 §3.5](audit-02-architecture-deep-dive.md)):
- *Edge vs. network:* a cascade is a network-level computation, so edge nodes do **local
  sensing + single-node inference and forward features**; the **network cascade is computed
  centrally**. We do not claim "the whole brain on a Pi."
- *Offline vs. Claude:* the LLM is **template-first and asynchronous** — alerts fire from
  deterministic templates instantly; Claude only enriches phrasing when reachable. "Offline-
  capable" and "Claude in the pipeline" are reconciled, not both headline claims.

---

## 5. Data reality

*(Fact about the world, independent of the event — [audit-01 §3](audit-01-screening-feasibility.md).)*

- **There is no official public NTES API.** NTES is a passenger enquiry portal; scraping it
  is brittle, rate-limited, ToS-grey, and **will break on stage**.
- The real backbone is **RTIS** (ISRO/IRNSS GPS, ~30 s updates) → **COA** (Control Office
  Application) → **FOIS** (freight) — all **internal** to Indian Railways, not open to
  developers.
- Therefore the **digital twin is the primary data source** (deterministic, never rate-
  limited, runs with the network cable unplugged). We ship a **mocked COA/RTIS adapter** as
  the production integration point, and treat any NTES scrape as optional enrichment behind
  a circuit-breaker. *The absence of an open feed is itself a finding we volunteer.*

---

## 6. ML engine

- **One spatio-temporal GNN**, not GNN + LSTM (which would disagree —
  [audit-02 §1.3](audit-02-architecture-deep-dive.md)). Workhorse: **Graph WaveNet** or
  **DCRNN** (diffusion ≈ cascade); the **graph-conditioned Hawkes / neural point process**
  framing is our depth signal ([audit-03 §1](audit-03-worth-winning-upgrades.md)).
- **Heterogeneous graph** with edge types `{block-conflict, platform-conflict, rake-link,
  crew-link, loco-link}`. The **rake-link** (same physical trainset turning around as a
  later service) is a top cascade source v0 missed entirely
  ([audit-02 §3.2](audit-02-architecture-deep-dive.md)).
- **Learned edge weights**, not hand-set — with a **with-vs-without-rake-link ablation** as
  the single best proof slide ([audit-02 §3.4](audit-02-architecture-deep-dive.md)).
- **Conformal prediction** for distribution-free intervals + a reliability curve
  ([audit-03 §4](audit-03-worth-winning-upgrades.md)).
- **GNNExplainer / attention attribution** → a one-line *why* per cascade
  ([audit-03 §5](audit-03-worth-winning-upgrades.md)).
- **OOD detection → simulator fallback** for black-swan disruptions with no historical
  analog ([audit-04 §2](audit-04-flaws-edge-cases.md)).
- **Tail-aware loss** (focal / cost-sensitive) + tail-recall evaluation, because the
  cascades that matter are rare ([audit-04 §6](audit-04-flaws-edge-cases.md)).

---

## 7. Re-routing realism — the center of gravity

Because proactive re-routing *is* the product, its realism gaps are correctness, not polish
([audit-01 §4–§5](audit-01-screening-feasibility.md), [audit-03 §3](audit-03-worth-winning-upgrades.md), [audit-04 §7](audit-04-flaws-edge-cases.md)):

- **Ticket validity:** a reserved ticket is **not** valid on another train. We model
  validity, WL/Tatkal, and availability — mocking IRCTC **honestly** where we lack access.
- **Capacity-aware / no herding:** allocation is a capacity-constrained assignment /
  congestion game; recommendations spread **fractionally** across alternatives by live
  capacity. Never recommend a full train; degrade to an honest "wait" ETA when no good
  option exists.
- **Close the loop:** accepted re-routes feed back as demand so we don't create a second
  cascade onto the alternative.
- **Honest latency window:** single-digit minutes on public data; the advertised 20–40 min
  exists only on the RTIS feed we can't access. We frame value as *"earlier than the
  official announcement,"* not a fixed minute count.
- **Demo proof:** two passengers, same disruption, **different feasible** re-routes.

---

## 7.5 Passenger Helpline & Grievance Redressal

A support layer inside the same app, for the questions and complaints prediction can't answer.

**What the passenger does:** opens the helpline and asks by **text or regional-language
speech** ("मेरी ट्रेन की AC काम नहीं कर रही", spoken in Hindi/Bengali/Tamil/…).

**What the system does** (agentic pipeline — see [workflow.md Part A.2](workflow.md)):
1. **Transcribe** speech to text via regional-language ASR (Bhashini/ULCA primary, Whisper
   fallback); optionally translate to a working language.
2. **Understand** the query with an LLM agent — classify the grievance category and extract
   entities (PNR, train, station, coach).
3. **Fetch passenger details** from the PNR/profile (IRCTC mocked honestly).
4. **Open a tracked case** and **route it to the appropriate authority** (RPF, Medical,
   Sanitation, IRCTC Catering, Electrical, Operations, Commercial…) — RailMadad-style.
5. **Dispatch** the case to that authority (RailMadad/email adapter, mocked) and reply to the
   passenger (text, plus optional spoken reply via TTS) with the case id + department.

**My Queries:** every case is visible with its status — `open → in_progress → resolved`
(or `rejected`) — and its history.

**Design rules** (consistent with the rest of the system):
- **Structured fields are authoritative; the LLM only phrases.** Routing/dispatch use the
  classified category + extracted entities — a misrouted department is worse than a clumsy
  sentence (mirrors the template-first rule for alerts).
- **Mock honestly, design the real adapter.** Bhashini and RailMadad aren't openly turnkey, so
  they sit behind clean adapters and are mocked until access exists.
- **Privacy.** Grievances are PII: store the minimum for status tracking, scope each passenger
  to their own cases, honour a retention policy ([audit-04 bonus](audit-04-flaws-edge-cases.md)).
- **Low confidence → general helpdesk**, never a guessed department.

Built by `services/helpline/` (agent · ASR/TTS · intent · authority routing · cases · dispatch),
exposed via `services/api` routers `helpline` + `queries`, surfaced in the passenger app.

---

## 8. Edge-case hardening (from [audit-04](audit-04-flaws-edge-cases.md))

| # | Failure | One-line fix |
|---|---|---|
| 1 | Feed outage → silent blindness | Store-and-forward + degradation ladder (live → dead-reckoning → schedule-prior) + staleness watermark |
| 2 | Black-swan with no analog | OOD flag → discrete-event simulator projects from first principles |
| 3 | GPS drift → phantom cascades | Map-matching + Kalman/particle filter; sensor fusion vs. track circuits |
| 4 | Weather as smooth feature | Model as **regime variable**; ingest caution-order/TSR; regime-stratified eval |
| 5 | Timetable revision → stale graph | Timetable-diff-triggered rebuild + drift monitoring |
| 6 | Tail under-prediction | Tail-aware loss + quantile outputs + simulator augmentation; evaluate tail recall |
| 7 | Re-route feedback loop | Capacity-aware fractional allocation; close the demand loop |
| 8 | Garbage/adversarial upstream | Validation/anomaly gate; quarantine to dead-letter, don't crash |
| 9 | Event-time vs processing-time | Event-time semantics + watermarks; carry data-age; discount stale inputs |
| 10 | Scale to all zones | Event-scoped k-hop subgraph inference; sparse/compiled graph; zonal partitioning |

---

## 9. Tech stack (hardened)

| Layer | Technology | Note |
|---|---|---|
| Primary data | **SimPy** discrete-event digital twin | deterministic, demo-safe |
| Prod data path | COA/RTIS adapter (mocked) | the real integration point |
| Streaming/buffer | **Redis Streams** | Kafka is "architecture theatre" for one zone ([audit-02 §3.6](audit-02-architecture-deep-dive.md)) |
| ML | **PyTorch Geometric** | Graph WaveNet/DCRNN, HeteroData, conformal, GNNExplainer |
| Re-routing | Python (capacity-constrained assignment) | core engine |
| LLM | **Claude API** (`claude-sonnet-4-6`) | template-first, async, phrasing only |
| Helpline ASR/NMT/TTS | **Bhashini/ULCA** (Whisper fallback) | regional-language speech in/out; mocked honestly |
| Grievance dispatch | **RailMadad-style** adapter (mocked) | category → authority routing + case tracking |
| Backend | **FastAPI** | REST + WebSocket + Corridor Risk API + OpenAPI `/docs` |
| Operator UI | **React + Mapbox GL JS** | heatmap + cascade chain (context) |
| Passenger UI | **Expo / React Native** (Android + iOS) + `expo-notifications` (FCM/APNs) | native app, reliable background push, primary surface |
| Storage | **PostgreSQL + TimescaleDB** | event-time delay storage, continuous aggregates |
| Graph store | PyG sparse adjacency (in-mem); **Memgraph/Neo4j** for scale | drop pure NetworkX beyond demo |
| Containers | **Docker + Docker Compose** | single-command setup |

---

## 10. Scope: in / mocked / Phase-2

- **In (build):** digital twin, ingestion + validation gate, heterogeneous graph, one
  ST-GNN + ablation, capacity-aware re-route, template-first alerts + async LLM, passenger
  app, operator heatmap, REST/WS API, graceful degradation, **helpline chatbot
  (text + regional-language speech) with authority routing + case tracking**.
- **Mocked (honestly):** COA/RTIS live feed, IRCTC availability/booking, FCM in some envs,
  **Bhashini ASR/TTS, RailMadad authority dispatch**.
- **Phase-2 (roadmap, not a gate):** operator dispatch optimizer (CP-SAT / Maskable-PPO on
  Flatland), IoT edge nodes (MQTT/LoRaWAN, axle counters, ONNX edge inference),
  multi-zone partitioning, multilingual alerts.

Honest scope is declared in `WHAT_WE_BUILT.md` (real / mocked / next).

---

## 11. Team roles (remapped onto hardened components)

| Member | Domain | Ownership in this architecture |
|---|---|---|
| Member 1 | ML / Model | ST-GNN (`ml/`), training, quantisation, ablation |
| Member 2 | ML / Data Eng | Hetero graph build (`data/graph/`), conformal/eval, historical calibration |
| Member 3 | Data Eng | Digital twin (`data/simulator/`), ingestion + validation gate (`data/ingestion/`), Redis Streams |
| Member 4 | Mobile / Frontend | Passenger app (Expo/React Native) + operator dashboard web (`frontend/`), push, **helpline chat + My-Queries screens** |
| Member 5 | Full-Stack / Backend | FastAPI + WS API (`services/api/`), re-route engine, worker, **helpline service** (agent/ASR/routing/cases), Docker |

---

## 12. Demo arc + the three killer questions

**4-minute arc** ([audit-03 §9](audit-03-worth-winning-upgrades.md)):
1. *(0:00–0:45)* Replay a real historical cascade on the section map — one delay blooms into
   6 stations over 90 min. "Nobody saw this coming."
2. *(0:45–2:00)* On the twin, inject the same delay; the ST-GNN lights up the same stations
   **before they fail**, with calibrated probabilities and a one-line *why*.
3. *(2:00–3:15)* **The moment:** the passenger is re-routed **before** the official
   announcement; two passengers get *different, feasible* routes.
4. *(3:15–4:00)* The one number ("re-routed 12 min before the announcement · 1,800
   passenger-minutes saved") + production path (RTIS/COA adapter ready).
5. *(4:00+)* Kill the live feed on stage → graceful degradation, not a lie.

**The three questions that decide the table** ([audit-00](audit-00-verdict.md)):
1. *Where does real-time data come from in production?* → RTIS→COA via CRIS, not open; we
   validate on a calibrated digital twin and ship the COA adapter.
2. *I have a confirmed reserved ticket — how do I act on the re-route?* → we check validity
   and live availability, surface fresh-booking/Tatkal, never recommend a full train.
3. *How is this different from the ixigo alert?* → theirs is reactive single-train; ours is
   the **network cascade** on the dependency graph, re-routing **before** the announcement.

---

*CascadeGuard — FAR AWAY 2026 · Railways Track. See [workflow.md](workflow.md) for the
runtime pipeline and the team build sequence.*
