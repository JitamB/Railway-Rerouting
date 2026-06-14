# What We Built — CascadeGuard

**CascadeGuard** is a real-time delay-cascade predictor and proactive passenger re-routing engine
for Indian Railways. When one train is held, delays ripple along shared tracks, platforms, rakes,
crews and locos. CascadeGuard predicts that ripple *before* it happens and re-routes affected
passengers — before the station announcement — while a multilingual helpline turns spoken
grievances into routed, trackable cases.

This document is the honesty contract: what is **real**, what is **mocked** (and why), and what
is **next**. Nothing below is hand-waved.

---

## The 4-minute demo arc (runs with the cable unplugged)

```bash
bash infra/scripts/setup.sh        # one-time: venv + editable installs
bash infra/scripts/run_demo.sh     # the whole arc, offline, ~8s cold
```

1. **Contracts locked** — every cross-service message validates against a frozen JSON schema.
2. **Digital twin** — a SimPy section (PNBE → MGS → BSB) replays an OHE-failure cascade; 94
   train-delay-minutes over 7 stops, peak 18 min.
3. **ST-GNN forecast** — the model, running locally, predicts downstream risk (BSB 0.87) with a
   calibrated delay interval and a one-line *why* (`100% rake-link 12301→12302`).
4. **Worker pipeline** — that twin delay flows end-to-end to a push: inference → cost-sensitive
   trigger → capacity-aware re-route (`15049`) → templated alert → delivery.
5. **Helpline** — a spoken Hindi grievance (“B4 coach mein ek lawaris bag”) → routed to **RPF** →
   a tracked case visible under My Queries.
6. **Five e2e scenarios** pass on the twin with no network.

**Proof slide** (separate, retrains two models): `python -m cascadeguard_ml.eval.ablation` →
removing the rake-link edge drops **tail recall 1.00 → 0.50** (Brier 0.041 → 0.086). The topology
*measurably* matters; it isn't decoration.

---

## What's real

**The moat — ST-GNN on a heterogeneous dependency graph.** Temporal dilated convolutions +
per-relation message passing (block / platform / rake / crew / loco links) with learnable
relation gates, predicting risk + delay on service nodes. The rake-link ablation is a genuine,
reproducible result, not a claim.

**Honest uncertainty.** Split-conformal prediction intervals (calibrated coverage), a
Mahalanobis OOD detector that falls back to the schedule prior on out-of-distribution input, and
an occlusion-based explainer that attributes the cascade to the responsible edge.

**Decisioning, not a magic threshold.** The notifier fires on a cost-sensitive utility decision
using the conformal interval as confidence — expected passenger-minutes saved vs. expected
false-alarm cost.

**Capacity-aware re-routing.** Deterministic alternative-train enumeration + a capacity-weighted
allocator that spreads passengers across feasible trains (no herding, never recommends a full
train, honest “WAIT”) with a demand-feedback loop.

**Graceful degradation.** Live → dead-reckoning → schedule-prior, combined with the model’s OOD
fallback, every prediction carrying a “based on data N s old” staleness watermark — never blank,
never a confident wrong answer.

**The serving spine.** A worker pipeline (buffer → k-hop subgraph → inference → trigger →
re-route → alert → push) and a FastAPI surface (REST + a WebSocket that streams per-station
deltas + an open Corridor Risk API), responses carrying the watermark.

**Two polished frontends.** A native Expo/React-Native passenger app (PNR registration, the
re-route card with risk/interval/alternatives/seat-reality/why/data-age, a multilingual helpline
chat) and a control-room operator dashboard (a corridor heatmap that lights up live over the WS,
a cascade chain with per-hop *why*, station drill-down).

**Helpline subsystem.** Rule-based multilingual understanding (English + romanized Hindi) →
authority routing (misroute-averse: low confidence → general helpdesk) → an owner-scoped case
lifecycle with history → dispatch reference.

**108 automated tests** across every package, plus contract validation and the 5 e2e demo
scenarios — all offline.

---

## What's mocked — honestly, behind clean adapters

Each mock is deterministic, clearly labelled, and sits behind the same interface the real adapter
will implement. Mocking is a *deliberate* choice where the real system isn't openly accessible.

| Area | Mocked as | Why | The real adapter |
|---|---|---|---|
| Live train feed (COA/RTIS, NTES) | The **digital twin** is the primary source | No open realtime API; the twin is deterministic and demo-safe | `cascadeguard_ingest/adapters/{coa_rtis,ntes_scrape}.py` already shaped to the wire contract |
| Weather / TSR regime | Static regime signal | OpenWeather key optional | `adapters/weather_tsr.py` |
| Seat availability (IRCTC/PRS) | Deterministic `live_availability` | PRS isn't openly API'd; a wrong “just board it” loses trust | swap the mock in `reroute-engine/ticketing.py` |
| Push delivery (FCM/APNs) | `mock-fcm-…` id; lazy real path | Firebase creds not in the demo | `notifier/fcm.py` activates with `FCM_*` env |
| LLM phrasing (Claude) | Template-first; LLM only *enriches* | Offline-capable; safety fields stay templated | `llm-agent/client.py` (`AsyncAnthropic`, `ANTHROPIC_API_KEY`) |
| Speech ASR/NMT (Bhashini/Whisper) | Decodes the clip as text; passthrough NMT | No turnkey all-language API | `helpline/asr.py` (Bhashini/ULCA or Whisper) |
| Spoken replies (TTS) | Disabled (text-only) | — | `helpline/tts.py` (`enabled` flag) |
| Grievance dispatch (RailMadad) | Deterministic `RM-…` reference | Not openly API'd | `helpline/dispatch.py` |
| Case persistence | In-memory store | Demo runs without Postgres | mirrors `infra/db/init.sql`; same functions write the tables |
| Operator map | Self-contained SVG corridor | Runs token-free | `mapbox-gl` kept as a dep; GL layer keyed on the same risk |

---

## What's next (productionization)

- **Real feeds:** wire COA/RTIS + NTES behind the existing adapters; the circuit breaker and
  store-and-forward buffer are already in place.
- **Persistence:** point the case store and the prediction store at TimescaleDB/Postgres (schema
  shipped in `infra/db/init.sql`); the API’s read interface is unchanged.
- **Push + accounts:** add the push-token registration endpoint, Firebase creds, PNR auth.
- **Multilingual rigor:** swap in Bhashini ASR/NMT/TTS and *verify* each language pair; keep
  safety-critical fields templated.
- **Scale:** the single-zone build uses Redis Streams deliberately; multi-zone moves to a
  partitioned log and per-zone workers.
- **Geographic map:** drop the Mapbox GL layer over the SVG corridor with a token.

---

## Run it

```bash
# offline demo arc (no Docker, no keys, no network)
bash infra/scripts/setup.sh
bash infra/scripts/run_demo.sh

# live surfaces (optional)
uvicorn cascadeguard_api.main:app --reload            # REST + WS + Corridor API → /docs
cd frontend/operator-dashboard && npm run dev          # :3001 — inject a delay, watch it light up
cd frontend/passenger-app && npx expo start            # native app via Expo Go

# the proof slide
python -m cascadeguard_ml.eval.ablation
```
