# `data/simulator/` — Digital Twin (PRIMARY data source)

A **discrete-event simulator** (SimPy) of one real railway section: stations, block sections,
platforms, headways, and a realistic timetable. This is the spine of the whole project, not a
toy ([audit-03 §2](../../docs/audit-03-worth-winning-upgrades.md)).

It plays **three roles**:
1. **Primary data source** during dev and on stage — deterministic, never rate-limited, runs
   with the network cable unplugged.
2. **Counterfactual engine** — "without CascadeGuard you're stranded; with it you were
   re-routed before the delay was announced."
3. **Scenario generator** — inject derailments, OHE failures, fog regimes, freight conflicts
   to produce rare-event training/validation data no log contains
   ([audit-04 §2/§6](../../docs/audit-04-flaws-edge-cases.md)).

Calibrate baseline running against a static historical NTES dump so it matches reality.

## Modules (`cascadeguard_sim/`)

| Module | Responsibility |
|---|---|
| `engine.py` | SimPy discrete-event loop; advances trains over block sections, emits events |
| `network.py` | Section topology: stations, block sections, platforms, headways |
| `timetable.py` | Scheduled services, rake links, crew/loco turnarounds |
| `scenarios.py` | Disruption injectors (derailment, OHE failure, fog regime, freight conflict) |
| `calibration.py` | Fit baseline running to a historical NTES dump |

Section config lives in `config/section.example.yaml`.

## Implementation status (Stage 1, Steps 3–6 — done)
Test: `pytest data/simulator/tests` · visual: `python run_twin.py --scenario ohe_failure --horizon 160`.

- `network.py` ✅ stations/blocks from YAML · `timetable.py` ✅ services + rake/crew/loco links
  (`ServiceLink`) · `engine.py` ✅ SimPy loop emitting event-time `TrainEvent`s under
  headway/platform/rake-turnaround constraints · `scenarios.py` ✅ OHE/fog injectors ·
  `calibration.py` ✅ per-station delay bias from a historical dump (documented defaults if none).
- Note: the schedule is **time-compressed** (sim-minutes) so a full cascade fits `run(120)`;
  `length_km` stays real for the graph/plausibility layers. `TrainEvent.event_time` is sim-minutes.
