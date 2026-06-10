# Audit 03 — "Worth Winning" Upgrades

> Concrete advanced features, cutting-edge architectures, optimization, IoT, and data pipelines to turn a competent project into a showstopper — plus how to weaponize them in a 3–5 minute final pitch.
>
> **Context (v2):** Direction is **harden the passenger-focused concept**. The headline upgrades below serve that. The operator dispatch-optimizer (v1's "non-negotiable") is now an **optional ambition path** — kept in §7 for teams who want to broaden scope, not on the critical path.

Every item is buildable in a hackathon window and chosen for **maximum juror impact per engineering hour**. Ranked by ROI for the passenger-focused build.

---

## 1. Upgrade the predictive core: one Spatio-Temporal GNN (replaces GNN + LSTM)

**Why it wins:** Collapses two disagreeing models into one coherent, citable, state-of-the-art architecture — and removes the consistency SPOF (`audit-02 §1.3`). This is your moat; make it sharp.

Pick one (all have mature PyG/open implementations):

- **DCRNN (Diffusion Convolutional RNN)** — purpose-built for traffic forecasting on graphs; models delay as *diffusion* over the network. The "diffusion" framing maps perfectly onto "cascade." Strong default.
- **Graph WaveNet** — learns the adjacency (the *adaptive adjacency matrix*) so you don't hand-set edge weights — directly fixes `audit-02 §3.4`. Best when topology is uncertain.
- **TGN (Temporal Graph Networks)** — event-stream-native; ideal if each delay report is a timestamped event. Most "real-time" story.
- **Graph-conditioned Hawkes / neural point process** — explicitly models "an event at A increases the hazard of events at downstream nodes." This *is* a cascade in the statistical-physics sense. Highest novelty, slightly higher risk.

**Recommendation:** Graph WaveNet *or* DCRNN as the workhorse; mention the Hawkes framing as your depth signal.

**Make the graph heterogeneous** (from `audit-02 §3.2`): edge types `{block-conflict, platform-conflict, rake-link, crew-link, loco-link}`. Use a **heterogeneous GNN** (PyG `HeteroConv` / RGCN-style relational weights). The **rake-link** edge alone (same physical trainset turning around as a later service — a top cascade source) will measurably improve accuracy and is a "we understand railways, not just graphs" credibility marker. Run a **with-vs-without-rake-link ablation** — it's your single best proof slide.

---

## 2. Solve data, demo, and validation at once: the Digital Twin

**Why it wins:** It simultaneously (a) eliminates the no-NTES-API dependency (`audit-01 §3`), (b) generates rare-event training data you can't get from logs, (c) becomes the **counterfactual engine** for the killer demo, and (d) lets you run the entire pitch with the network cable unplugged.

- Build a **discrete-event simulator** (Python **SimPy**, or build on **Flatland** for the grid-rail abstraction) of one real section: stations, block sections, platforms, headways, a realistic timetable.
- Calibrate it against a **static historical NTES log dump** so its baseline running matches reality.
- It plays three roles:
  1. **Primary data source** during dev and on stage (deterministic, never rate-limited).
  2. **Counterfactual engine:** "without CascadeGuard you're stranded; with it you were re-routed before the delay was announced."
  3. **Scenario generator:** inject derailments, OHE failures, fog regimes, freight conflicts to stress-test (covers `audit-04 §2, §6`).

This flips "your data source is fake" into "we built a calibrated digital twin because the real feed (RTIS→COA) isn't open — here's the production adapter for when it is." **This is non-negotiable for a credible passenger-focused demo.**

---

## 3. Harden re-routing into something no commodity app has (your center of gravity)

Proactive cascade-aware re-routing is your differentiator — make it the *smart* version:

- **Capacity-aware / congestion-safe allocation.** Treat alternative-train assignment as a **congestion game / capacity-constrained assignment** so you don't herd everyone onto the 13:55 and create a second cascade (`audit-04 §7`). Recommend **probabilistically / fractionally** across alternatives, weighted by live capacity.
- **Ticketing reality** (`audit-01 §5`): model reserved-ticket validity, WL/Tatkal, and availability. Mock IRCTC honestly if no access — but *model* it, don't ignore it.
- **Close the loop:** feed accepted re-routes back as demand so the next recommendation accounts for filling seats.
- **Demo proof:** show two passengers with the *same* disruption getting *different, feasible* re-routes. That 20 seconds beats any heatmap.

---

## 4. Calibrated uncertainty: conformal prediction

**Why it wins:** Jurors with stats backgrounds reward calibrated uncertainty over point predictions, and it's cheap to add.

- Wrap the spatio-temporal GNN with **conformal prediction** for **distribution-free intervals** with guaranteed coverage ("90% of the time the true delay falls in [a, b]").
- Show a **reliability/calibration curve**: "our 70% predictions happen 70% of the time" is a 10-second credibility kill-shot against teams showing only accuracy.
- Feeds a **cost-sensitive notification trigger** (`audit-02 §4`): notify on *expected* passenger-minutes saved with known confidence, not a magic 65%.

---

## 5. Explainability: GNNExplainer + attention attribution

**Why it wins:** "Why should I trust this alert?" is a guaranteed question. Attribution answers it and showcases the graph.

- Use **GNNExplainer / attention weights** to attribute each cascade prediction: *"This cascade is 60% driven by the rake-link between 12301↔12302 and 30% by a platform conflict at PNBE."*
- Pair every passenger alert with a one-line *why* — it converts a scary push into a trustworthy one.

---

## 6. Data-pipeline upgrades

- **Event sourcing with event-time semantics:** keep delay events immutable and time-stamped so "current delay" is never computed from a stale clock (`audit-04 §9`), and so you can replay cascades for the demo.
- **TimescaleDB** (already chosen — good) with **continuous aggregates** for dashboard rollups.
- **Drift monitoring:** log predicted-vs-actual; alert on calibration drift; trigger graph rebuild on timetable revisions (`audit-04 §5`).
- **Synthetic rare-event augmentation** from the simulator to fix tail under-prediction (`audit-04 §6`).

---

## 7. Optional ambition: an operator decision layer (Phase-2, not a gate)

*You chose to harden the passenger focus, so this is explicitly off the critical path.* But if the build goes fast and you want a higher ceiling / a second wow moment, this is the highest-impact expansion — and it reuses your GNN directly:

- A **prescriptive layer** that turns cascade risk into a recommended **operator action** (hold / precedence / platform reassignment), via **OR-Tools CP-SAT** (deterministic, explainable) or **Maskable-PPO RL** (anchor credibility on the **Flatland** rescheduling benchmark).
- The GNN's cascade risk becomes the optimizer's **cost/priority signal** — the novel coupling: predictor teams lack the optimizer, OR teams lack cascade-aware costs.
- **Decision:** only attempt this once §1–§5 are solid. A flaky half-optimizer is worse than a polished passenger product. Treat it as a roadmap slide unless it demonstrably works live.

---

## 8. IoT / edge layer — only if you do it correctly (otherwise a Phase-2 schematic)

The doc's Phase-4 hardware is a liability if hand-waved, an asset if precise. If you build it:

- **Protocol:** **MQTT over LoRaWAN** for constrained junction nodes (not vague "LoRa radio"); NB-IoT as cellular fallback. Be specific — jurors notice.
- **Ground-truth sensing:** ultrasonic platform occupancy is weak; the real railway primitives are **axle counters** and **track circuits** for block occupancy. Reference those — domain literacy.
- **Edge inference:** **ONNX Runtime** on a **Raspberry Pi / Jetson Nano**-class node doing **local single-node inference + feature forwarding**; the **network cascade is computed centrally** (resolves the `audit-02 §3.5` contradiction).
- **Honest scoping:** present hardware as Phase 2 with a credible BOM and protocol stack. A clean schematic + protocol diagram earns more than a flaky breadboard.

---

## 9. Pitch wow-factor — engineering the 3–5 minute jury arc (passenger-centric)

Jurors remember **one number and one moment.** Engineer both.

1. **(0:00–0:45) Make the problem visceral.** Replay a *real* historical cascade on the section map — one delay at a junction blooms into 6 downstream stations over 90 min. No narration. End on: *"Nobody saw this coming. 23 million passengers a day ride on top of it."*
2. **(0:45–2:00) CascadeGuard predicts — and shows its work.** Live on the digital twin: inject the same initial delay; the spatio-temporal GNN lights up the *same* downstream stations **before they fail**, with calibrated probabilities and a one-line *why* (explainability). Pause on the cascade chain — *this* is the moat, make them look at it.
3. **(2:00–3:15) THE MOMENT — the passenger is saved before the railway reacts.** On a phone, the proactive re-route lands **before the official delay is even announced**. Side by side: *"without CascadeGuard, this passenger is stranded for 90 minutes; with it, they're on an alternative that arrives 18 minutes late."* Show two passengers getting *different, capacity-feasible* routes — proof it's not a broadcast.
4. **(3:15–4:00) The one number + production path.** Big on screen: **"Re-routed 12 minutes before the official announcement · 1,800 passenger-minutes saved on this one cascade."** Then 20 seconds on credibility: GNN moat (with the ablation), calibrated, explainable, validated on a calibrated twin, RTIS/COA adapter ready for production.
5. **(4:00–4:30, if time) Robustness flex:** kill the live feed on stage and show the system **degrade gracefully** instead of lying (`audit-04 §1`). Demonstrated failure-handling is rarer and more memorable than another green dashboard.

### Rules that win the room
- **Never depend on the live network on stage.** Run the twin; the live NTES feed is a *bonus tab*, never the spine. This single discipline saves more demos than any feature.
- **Lead with the cascade graph and the "before the railway" moment**, not the dashboard. Bury the commodity layers (single-train prediction) in the plumbing.
- **Volunteer the honesty.** Say what's mocked (IRCTC availability, live COA). Pre-empting the gotcha reads as senior; getting caught reads as junior.
- **One ablation slide** ("with rake-link edges vs without"). Proof you measured, not just built.
- **Close on the differentiator sentence:** "No consumer app models the network cascade, and none re-routes you before the railway announces the delay. That's CascadeGuard."

---

## Priority order (if time is short)

1. **Digital twin** — without it your demo and data story collapse. *Non-negotiable.*
2. **Unified spatio-temporal GNN + heterogeneous edges (rake-link) + ablation** — the moat, made legible.
3. **Hardened, capacity-aware re-routing + ticketing realism** — your center of gravity.
4. **Counterfactual demo + the one number** — what they remember.
5. **Conformal intervals + explainability** — cheap rigor that beats flashier teams.
6. Operator decision layer (§7) — *only* if 1–5 are solid; else a roadmap slide.
7. IoT layer — else a clean Phase-2 schematic.
