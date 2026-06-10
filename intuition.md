# CascadeGuard 🚆
### Real-Time Delay Cascade Predictor & Passenger Re-Routing Engine for Indian Railways

> *"Every delayed train doesn't just affect its own passengers — it starts a chain reaction. CascadeGuard breaks the chain before it begins."*

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [What CascadeGuard Does](#2-what-cascadeguard-does)
3. [Core Features](#3-core-features)
4. [System Architecture](#4-system-architecture)
5. [AI & ML Engine](#5-ai--ml-engine)
6. [Data Sources](#6-data-sources)
7. [Tech Stack](#7-tech-stack)
8. [Differentiators — Why This Is Not Another Delay Predictor](#8-differentiators)
9. [Demo Walkthrough](#9-demo-walkthrough)
10. [Roadmap & Future Extensions](#10-roadmap--future-extensions)
11. [Team Roles](#11-team-roles)

---

## 1. Problem Statement

Indian Railways carries **23 million passengers daily** across one of the world's largest rail networks. A single disruption — a signal failure, an engine fault, a track obstruction — rarely stays local. It propagates: a delayed train occupies a platform, blocking the next arrival, which in turn pushes freight crossings, which holds up a third train, and so on.

This **cascade effect** is the silent multiplier behind India's most disruptive delay events. Yet the current passenger-facing infrastructure offers no:

- Real-time cascade propagation model
- Passenger-specific re-routing guidance issued *before* they're stranded
- Probabilistic risk scores visible to station operators before the cascade matures
- Open API for third-party apps (travel aggregators, corporate travel desks) to consume

Existing solutions (NTES, IRCTC alerts) are reactive — they notify passengers *after* the delay is confirmed, by which time the re-routing window has often closed.

**CascadeGuard is proactive.** It predicts the cascade, quantifies the risk at each downstream station, and gives passengers and operators a decision window of 20–40 minutes.

---

## 2. What CascadeGuard Does

At its core, CascadeGuard continuously monitors the live position and status of trains across a railway zone, models the dependency graph between stations and platforms, and runs a two-layer ML inference pipeline that answers two questions in real time:

1. **"If this train is currently X minutes late, which downstream stations are at risk, and by how much?"**
2. **"What is the best alternative route/train for Passenger Y right now, expressed in plain language?"**

The answer to Question 1 is delivered to **station operators** as a live risk heatmap.
The answer to Question 2 is pushed to **passengers** as a notification on their phone, in their language, before they even know there's a problem.

---

## 3. Core Features

### 3.1 Live Cascade Risk Heatmap (Operator Dashboard)
- Real-time station-level delay propagation risk scores (0–100%) updated every 60 seconds
- Interactive map of the railway zone with colour-coded station nodes (green → amber → red)
- Cascade chain visualisation: "Train 12301 → Delay at Patna Jn → Risk propagates to Mughal Sarai (71%), Varanasi (54%), Prayagraj (38%)"
- One-click drill-down into any station to see which trains are at risk and their estimated new arrival windows
- Historical cascade replay — review any past event's propagation timeline

### 3.2 Passenger Re-Routing Engine (PWA / Mobile)
- Passengers register their active PNR on the lightweight PWA
- System monitors their train and triggers push notifications when cascade risk exceeds a configurable threshold (default: 65%)
- Notification includes: current delay estimate, probability of further worsening, and 1–3 concrete alternative trains with platform, departure time, and estimated arrival at destination
- Guidance is generated in plain language by an LLM layer on top of the model output ("Your 14:30 Rajdhani has a 71% chance of 40+ min delay. The 13:55 intercity from Platform 4 reaches Howrah only 18 minutes later.")
- Works offline after first load; push notifications delivered via FCM even when app is closed

### 3.3 Station Dependency Graph (Proprietary Data Artifact)
- A directed graph where each edge encodes: "A delay at Station A, of type T (platform block / freight crossing / crew change), propagates to Station B with coefficient W"
- Built from publicly available Indian Railways zone schedules and historical delay patterns
- The graph is CascadeGuard's core IP — it is what makes the predictions station-topology-aware rather than just time-series extrapolations
- Exportable as GeoJSON + GraphML for downstream integrations

### 3.4 Corridor Risk API (Open REST API)
- Authenticated REST endpoints for third-party apps to query live cascade risk by:
  - Train number → list of at-risk downstream stations
  - Station code → incoming trains with delay probability and ETA range
  - Zone → aggregate corridor health score
- Designed for consumption by travel aggregators (MakeMyTrip, Ixigo), corporate travel tools, and state transport authorities
- Rate-limited, documented with OpenAPI spec, and comes with a sandbox environment pre-loaded with simulated data

### 3.5 Predictive Maintenance Signal (Bonus Layer)
- Trains that repeatedly appear as cascade *originators* (not just victims) are flagged for infrastructure review
- Pattern: if Train X causes cascade events at Station Y disproportionately often on a given day/time/weather combination, the system surfaces this to operators as a recurring structural risk
- Not a maintenance system in itself — a signal layer that feeds into existing maintenance workflows

---

## 4. System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     DATA INGESTION LAYER                         │
│  NTES Live API   │  OpenWeatherMap   │  Station Graph (Static)   │
│  (train positions)│  (route weather)  │  (platform dependencies)  │
└────────┬─────────┴────────┬──────────┴──────────────┬────────────┘
         │                  │                          │
         ▼                  ▼                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                    STREAM PROCESSING LAYER                        │
│              Apache Kafka  /  Redis Pub-Sub                       │
│         (event streaming, delay event triggers, buffering)        │
└─────────────────────────────┬────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐
│  Graph Neural   │  │  LSTM Corridor  │  │   LLM Re-Routing     │
│  Network (GNN)  │  │  Delay Model    │  │   Agent (Claude API) │
│  Cascade spread │  │  Time-series    │  │   Natural language   │
│  across station │  │  per corridor   │  │   guidance generator │
│  topology       │  │                 │  │                      │
└────────┬────────┘  └────────┬────────┘  └──────────┬───────────┘
         └────────────────────┼───────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      OUTPUT & SERVING LAYER                       │
│  Operator Dashboard  │  Passenger PWA  │  REST API  │  WebSocket │
│  (React + Mapbox)    │  (Next.js PWA)  │  (FastAPI) │  live feed │
└──────────────────────────────────────────────────────────────────┘
```

**Edge deployability:** The GNN and LSTM models are quantised (INT8) and sized to run on a laptop CPU or Raspberry Pi 5, with no cloud inference required. This is a deliberate design decision — many Indian railway sections have unreliable internet connectivity.

---

## 5. AI & ML Engine

### 5.1 Graph Neural Network — Cascade Propagation Model
- **Purpose:** Given an initial delay event at Station A, predict the probability and magnitude of delay propagation at each downstream station within a 2-hop neighbourhood
- **Architecture:** GraphSAGE (inductive, scales to unseen stations) with edge attributes encoding: platform dependency type, scheduled crossing time delta, historical propagation coefficient
- **Training data:** 5+ years of historical NTES delay data, mapped onto the station dependency graph
- **Output:** Per-station cascade probability vector, updated on every new delay event

### 5.2 LSTM — Corridor Delay Forecaster
- **Purpose:** Time-series prediction of a specific train's delay at each upcoming station, conditional on current delay and weather features
- **Architecture:** 2-layer LSTM with attention, trained per corridor cluster (corridors with similar traffic density grouped together for data efficiency)
- **Features:** Current delay (minutes), weather severity score, time-of-day, day-of-week, is-holiday, section type (HDN / branch)
- **Output:** Predicted delay at each upcoming station with a confidence interval

### 5.3 LLM Re-Routing Agent
- **Purpose:** Convert raw model output (probability scores, alternative train schedules) into actionable, passenger-appropriate guidance
- **Integration:** Claude API (claude-sonnet-4-6), called only when cascade risk crosses the notification threshold — not on every inference cycle
- **Prompt design:** Structured input includes passenger's origin/destination, current train status, top-3 alternative trains from a deterministic routing query, and time sensitivity context
- **Output:** 2–3 sentences of plain-language guidance with specific platform and departure time
- **Why LLM here and not earlier:** The ML models handle prediction (speed-critical, runs locally). The LLM handles communication (quality-critical, called sparingly). Clear separation of concerns.

---

## 6. Data Sources

| Source | Data Type | Update Frequency | Access |
|---|---|---|---|
| NTES (National Train Enquiry System) | Live train positions, current delays | Every 2 minutes | Public API / scrape |
| Indian Railways zone timetables | Scheduled arrivals, platform allocations | Static (weekly refresh) | Open data / PDF parse |
| OpenWeatherMap API | Weather along route (rain, fog, wind) | Hourly | Free tier (1000 calls/day) |
| OpenRailwayMap | Track topology, station coordinates | Static | Open data (ODbL) |
| Historical NTES delay logs | Training corpus for ML models | One-time batch pull | Public / Kaggle datasets |

All data sources are either open, free-tier, or publicly scrapeable. No proprietary data partnerships required for a working prototype.

---

## 7. Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Data streaming | Apache Kafka (local) / Redis Pub-Sub | Event-driven architecture; delay events as first-class messages |
| ML — GNN | PyTorch Geometric | Best ecosystem for GraphSAGE; good quantisation support |
| ML — LSTM | PyTorch + Lightning | Fast iteration; INT8 quantisation via torch.ao |
| LLM layer | Claude API (claude-sonnet-4-6) | Best instruction-following for structured → natural language |
| Backend API | FastAPI (Python) | Async, OpenAPI auto-docs, easy WebSocket support |
| Operator dashboard | React + Mapbox GL JS | Real-time map rendering; WebSocket state updates |
| Passenger PWA | Next.js + FCM | Offline-first, push notifications, installable |
| Database | PostgreSQL + TimescaleDB | Time-series extension for delay event storage |
| Graph storage | NetworkX (in-memory) + GraphML export | Fast traversal for cascade propagation queries |
| Containerisation | Docker + Docker Compose | Single-command setup for judges |

---

## 8. Differentiators

This section directly addresses why CascadeGuard is not a variation of existing delay-prediction GitHub repos.

**What already exists:**
Most public projects (Random Forest on historical data, LSTM per train, ARIMA + Prophet pipelines) answer: *"How late will Train X be at Station Y?"* — a single-train, single-outcome prediction. These are well-solved, well-published, and will flood the Railways track at this hackathon.

**What CascadeGuard does differently:**

| Dimension | Existing approaches | CascadeGuard |
|---|---|---|
| Unit of prediction | Single train delay | Network-level cascade propagation |
| Graph topology | Not modelled | Station dependency graph (custom-built, proprietary) |
| Beneficiary | Passive (passenger checks app) | Active (system pushes re-routing before passenger realises) |
| AI role | Prediction model = final output | Prediction model → LLM translation → actionable guidance |
| Deployability | Cloud-dependent | Edge-quantised models, offline-capable |
| Operator layer | None | Live heatmap + cascade chain visualisation |
| API | None | Open REST API for third-party consumption |
| Novel data artifact | Standard features | Station dependency graph as core IP |

The GNN operating on station topology is the single most defensible technical claim — no public hackathon project or open-source repo applies graph neural networks to the Indian Railways cascade problem. This is the moat.

---

## 9. Demo Walkthrough

The demo is structured to prove all engineering claims within 4 minutes.

**Minute 1 — The problem made visible:**
Show a historical cascade event (a real NTES log) replayed on the station map. Watch a single delay at one junction spread to 6 downstream stations over 90 minutes. No narration needed — the visual tells the story. End with: "This happens 40+ times a day across the Indian Railways network. Nobody sees it coming."

**Minute 2 — Live system, live data:**
Switch to the real-time dashboard pulling from NTES. Point to a train with a current 12-minute delay. Show the GNN computing cascade risk in real time — three downstream stations turn amber. Click into one station to show the cascade chain visualisation.

**Minute 3 — The passenger experience:**
On a phone, show the PWA. A push notification arrives (triggered by the live dashboard event): "Your 14:30 train has a 68% chance of 40+ min delay. Alternative: 13:55 intercity, Platform 4, arrives only 18 min later." Tap to see the full re-routing card. The guidance was generated by the LLM layer — speak to the model→LLM pipeline separation explicitly.

**Minute 4 — The technical proof:**
Show the GitHub repo. Scroll through the GNN training output (loss curves, validation accuracy). Show the model running locally: `python inference.py --station PNBE` and watch the cascade probability vector print to console. Show Docker Compose bringing the full stack up in under 2 minutes. End on the API docs page (`/docs`) — show the endpoints are real and queryable.

---

## 10. Roadmap & Future Extensions

### Phase 2 — Post-Hackathon (Months 1–3)

**Multi-zone coverage**
Expand the station dependency graph from a single zone (e.g. Eastern Railway) to all 18 Indian Railways zones. The GNN architecture is inductive — it generalises to unseen stations without retraining, making this primarily a data engineering task.

**Freight-passenger interaction layer**
Freight trains cause a disproportionate share of passenger delays because they share tracks with passenger services. Modelling freight crossings as a separate class of cascade originator would significantly improve prediction accuracy, particularly on non-HDN sections.

**Passenger demand forecasting integration**
During high cascade-risk periods, surface demand data (live ticket availability on alternative trains) to the re-routing engine so it doesn't recommend a train that's already fully booked. Requires IRCTC API access or a scrape layer.

### Phase 3 — Scaling (Months 4–12)

**Railway control room integration**
Build an operator-facing variant of the dashboard designed for Centralised Traffic Control (CTC) centres, with role-based access, alert acknowledgement workflows, and integration hooks for the existing National Train Control System.

**SIH / RDSO partnership pathway**
CascadeGuard's cascade propagation model and station dependency graph are directly relevant to the Indian Railways' push for AI-driven operations under Mission Raftaar. The open API design and open-source core are intentional — they make RDSO integration technically straightforward.

**Multilingual passenger alerts**
Replace the English-only LLM guidance with a language-routing layer that detects the passenger's preferred language from their device locale and generates alerts in Hindi, Bengali, Tamil, Telugu, or Marathi. The Claude API's multilingual capability makes this a prompt-engineering task, not a model re-training task.

**Hyperlocal last-mile connection**
When a passenger accepts a re-routed train that arrives at a different station, automatically surface connecting options (metro, bus, auto) for their new arrival point using GTFS feeds from city transit authorities.

### Phase 4 — Hardware Extension (Optional, High Impact)

**IoT edge nodes at high-risk junctions**
Deploy low-cost Raspberry Pi 5 nodes at the 20 highest-cascade-risk junctions identified by the model. Each node runs local GNN inference on platform sensor data (platform occupancy via ultrasonic sensors, train presence detection) and pushes to the central system with sub-second latency — eliminating the 2-minute NTES polling lag for the most critical stations.

**PCB design for junction sensor unit**
A custom PCB integrating: ESP32 microcontroller, LoRa radio (for areas without WiFi/4G), ultrasonic sensors for platform occupancy, and a GSM module for redundancy. This hardware layer turns CascadeGuard into a full-stack solution that doesn't depend entirely on NTES data quality.

---

## 11. Team Roles

| Member | Primary Domain | CascadeGuard Ownership |
|---|---|---|
| Member 1 | ML / Model Training | GNN architecture, training pipeline, model quantisation |
| Member 2 | ML / Data Engineering | LSTM corridor model, data pipeline, historical corpus processing |
| Member 3 | Data Engineering | Station dependency graph construction, NTES ingestion, Kafka setup |
| Member 4 | Full-Stack / PWA | Passenger PWA, push notification system, operator dashboard |
| Member 5 | Full-Stack / API | FastAPI backend, REST API, WebSocket server, Docker setup |

---

## Submission Checklist

- [ ] GitHub repository with meaningful commit history throughout build period
- [ ] `README.md` with architecture diagram, setup instructions, and `.env.example`
- [ ] `docker-compose.yml` for single-command full-stack setup
- [ ] Model training scripts + pretrained weights (or download script)
- [ ] OpenAPI documentation auto-generated at `/docs`
- [ ] 2–5 minute demo video with live system running on real NTES data
- [ ] `WHAT_WE_BUILT.md` — honest scope declaration (what works, what's mocked, what's next)

---

*CascadeGuard — FAR AWAY 2026 | Railways Track*
*Built with PyTorch Geometric · FastAPI · Next.js · Claude API · Indian Railways Open Data*