# Audit 04 — Flaws & Edge Cases (with technical fixes)

> 10 critical edge cases, deployment constraints, and environmental vulnerabilities the current intuition fails to address. Each has a concrete fix. A finals juror will probe several of these directly — prepared answers are the difference between "robust" and "toy."

The first five are the must-haves (the brief asked for ≥5); the next five are the depth that separates a winner from a finalist.

---

## 1. Connectivity loss / upstream feed outage → system goes blind

**Failure:** The whole pipeline depends on a single upstream feed (NTES). On unreliable rail-section connectivity (the doc's own justification for edge deployment) or an NTES outage/rate-limit, the system stops receiving data and produces **stale or no predictions** — silently, which is worse than failing loudly.

**Fix:**
- **Store-and-forward buffer** at ingestion (the Kafka/Redis layer is correctly placed for this) so transient gaps don't lose events.
- **Graceful degradation ladder:** live feed → last-known-position **dead reckoning** (propagate trains along schedule at last-known speed) → **schedule-only prior**. Never go blank; degrade with an explicit, surfaced confidence drop.
- **Staleness watermark:** every prediction carries "based on data N seconds old"; the UI greys out when N exceeds a bound. Honesty beats a confident wrong answer.
- **Production path:** the real feed (RTIS→COA) is more reliable than NTES scraping; design the adapter so the prototype's fragility isn't the product's fragility.

---

## 2. Cold-start / black-swan disruptions with no historical analog

**Failure:** The model is trained on *normal* delay patterns. The disruptions that matter most — **derailments, accidents, OHE (overhead equipment) failure, signal-cabin failure, agitations/blockades, cattle/obstruction, flooding** — are rare, structurally different, and may have **no historical analog**. A data-driven GNN will confidently under- or mis-predict exactly when stakes are highest.

**Fix:**
- **Physics/simulation fallback:** when an event doesn't match learned patterns (low model confidence / out-of-distribution flag), fall back to the **discrete-event simulator** (`audit-03 §3`) to project propagation from first principles (occupancy + headway + schedule), which needs no historical analog.
- **Out-of-distribution detection** (e.g., Mahalanobis/energy score on embeddings) to *know* you're off-distribution and switch modes + widen intervals.
- **Synthetic injection:** generate these rare scenarios in the simulator and train/validate on them so the model has *seen* the shape of a derailment cascade.

---

## 3. Sensor drift & GPS error → phantom cascades

**Failure:** GPS/IRNSS positions degrade in **tunnels, deep cuttings, dense yards, urban canyons** (multipath), and RTIS devices drift/fail. Raw positions can show trains **teleporting, stationary-when-moving, or off-track**. Fed straight into the GNN, these create **phantom delays and false cascades** — false alarms erode operator trust instantly.

**Fix:**
- **Map-matching** GPS to the track graph (snap to nearest feasible block) + **Kalman/particle filter** to smooth position/speed and reject physically impossible jumps.
- **Sensor fusion:** cross-check GPS against **track-circuit / axle-counter** occupancy (ground truth for "is a train here") where available; trust the interlocking over GPS on conflict.
- **Confidence-weighted ingestion:** low-quality fixes contribute less; a validation gate drops impossible readings before they reach the model.

---

## 4. Weather as a regime shift, not a feature → systematic model failure

**Failure:** The doc treats weather as a smooth "severity score" feature. In reality weather triggers **discrete operating-regime changes**: fog → **caution orders + speed restriction to ~60 km/h + detonators/fog-signals**; monsoon → **patrolling, TSRs, waterlogging**; extreme heat → **rail buckling speed cuts**. A model trained mostly on fair-weather data sees a **distribution shift** and degrades precisely during the high-delay periods it most needs to predict (North Indian winter fog is the canonical mass-delay event).

**Fix:**
- Model weather as a **regime/state variable** that switches the model's operating point (normal vs degraded) — e.g., a mixture/conditional model or regime-gated parameters — rather than one continuous input.
- **Ingest actual caution-order / TSR signals** where obtainable instead of inferring everything from a weather API.
- **Regime-stratified training & evaluation:** report metrics separately for fog/monsoon/normal so you don't hide failure in an averaged number — and so you can *show* fog-season robustness to the jury.

---

## 5. Data drift: timetable revisions invalidate the graph

**Failure:** The station-dependency graph and schedules are built once. But IR **revises zonal timetables** (and adds/cancels/reschedules trains, special trains, festival rakes) regularly. A static graph silently goes **stale** — edges, platforms, and crossings no longer match reality, and predictions decay without anyone noticing.

**Fix:**
- **Scheduled graph rebuild** triggered by timetable-diff ingestion (treat the timetable as a versioned input; rebuild on change).
- **Drift monitoring:** track predicted-vs-actual calibration over time; an accuracy/calibration drop flags a stale graph or model.
- **Inductive architecture pays off here** (GraphSAGE/Graph WaveNet generalize to new nodes) — but you still must *feed* the new topology; inductivity is not a substitute for refresh.

---

## 6. Class imbalance / tail under-prediction (the cascades that matter are rare)

**Failure:** The vast majority of delays **don't** cascade. Train naively and the model minimizes average loss by **predicting "no cascade"** and being right most of the time — while **missing the rare large cascades** that are the entire point. High accuracy, useless on the tail.

**Fix:**
- **Tail-aware loss:** focal loss / class-weighting / cost-sensitive learning that penalizes missed large cascades heavily.
- **Quantile or distributional outputs** (predict the upper tail, not just the mean) + **Extreme Value Theory** for tail-risk on the worst events.
- **Resample/augment** rare cascades from the simulator.
- **Evaluate on tail metrics** (recall on large-cascade events, not overall accuracy) and *show that metric*.

---

## 7. Re-routing feedback loop → you cause the next cascade

**Failure:** If the system pushes "take the 13:55 intercity" to **every** affected passenger, you **overload the alternative**, possibly causing *its* delay/overcrowding — a self-inflicted second cascade. The model assumes its recommendations don't change the system, but they do (the classic prediction-affects-outcome problem).

**Fix:**
- Model allocation as a **congestion game / capacity-constrained assignment**: spread recommendations **fractionally/probabilistically** across alternatives weighted by **live capacity**.
- **Close the loop:** feed accepted re-routes back as demand so the next recommendation accounts for filling seats.
- **Capacity guardrail:** never recommend a train already at/over capacity; degrade to "wait" with an honest ETA when no good option exists.

---

## 8. Adversarial / garbage upstream data

**Failure:** NTES/COA feeds intermittently emit **stale timestamps, zeroed positions, duplicated or out-of-order events, and impossible jumps.** Without a guard, these inject phantom events and corrupt the graph state — and a malicious actor on a scraped public endpoint could deliberately feed noise.

**Fix:**
- **Validation/anomaly gate** between ingestion and models: schema checks, physical-plausibility checks (Δposition ≤ vmax·Δt), de-duplication, monotonic event-time ordering.
- **Quarantine, don't crash:** route suspect events to a dead-letter queue; never let one bad record poison the live graph.
- **Confidence-weighted updates** so a single anomalous reading can't swing a node's risk.

---

## 9. Clock / event-time vs processing-time errors → "current delay" is wrong

**Failure:** "Current delay = now − scheduled" is computed against **whatever timestamp arrived**. If the feed is lagged (it is) or clocks skew, "current delay" is computed from **stale data** and every downstream prediction is anchored to a wrong present. Polling-based pipelines routinely conflate **when an event happened** with **when it was received**.

**Fix:**
- **Event-time semantics with watermarks** (Kafka Streams / Flink-style): reason about *when the train was actually there*, not when you heard about it.
- **Carry data-age** through the whole pipeline; discount predictions built on stale inputs.
- **NTP-discipline** any edge nodes; reject events whose timestamp implies negative or impossible latency.

---

## 10. Scale & deployment constraints the prototype hides

**Failure:** In-memory NetworkX + global 60-second recompute is fine for one zone and **silently infeasible** at the all-18-zones scale the roadmap promises (~7,300 stations, ~13,000 trains, temporal edges). The prototype's design choices don't survive their own success story — a juror who asks "does this scale to a zone, to the network?" exposes it.

**Fix:**
- **Event-scoped subgraph inference:** recompute only the *k*-hop subgraph around a new disruption, not the whole network every tick.
- **Compiled/sparse graph** for the hot path (PyG sparse adjacency) and a persistent graph store (Memgraph/Neo4j) if queries/HA are needed — drop pure in-memory NetworkX for anything beyond the demo.
- **Hierarchical / zonal partitioning:** model each zone as a subgraph with a thin **inter-zone boundary layer** (most cascades are intra-zone; inter-zone coupling is sparse). This both scales and matches IR's real operational structure (zones/divisions).
- **Be honest about prototype scope** in `WHAT_WE_BUILT.md`: "one section/zone, designed to partition to N."

---

## Bonus deployment realities worth a sentence each (jurors love these)

- **Security/ToS:** scraping NTES violates terms and risks IP bans mid-demo — another reason the simulator is primary and any scrape sits behind a circuit-breaker.
- **Privacy:** registering passenger PNRs means handling PII + journey data — mention consent, minimization, and that you don't store PNRs longer than the journey.
- **Multilingual correctness:** LLM alerts in Hindi/Bengali/Tamil/Telugu/Marathi must be *verified* — a mistranslated platform number is worse than no alert. Template the safety-critical fields (train no., platform, time) and let the LLM phrase only the prose.
- **Trust & override:** decision-support must let the controller **reject** a recommendation and log why — both a safety requirement and training signal.

---

## How to use this file in the demo

Don't bury these — **weaponize two of them**. Pick the connectivity-loss degradation ladder (§1) and the phantom-cascade sensor-fusion guard (§3), and *show* them: kill the feed live and show the system degrade gracefully instead of lying; inject a teleporting GPS point and show the validation gate catch it. Demonstrated robustness under failure is rarer — and more memorable — than another green dashboard.
