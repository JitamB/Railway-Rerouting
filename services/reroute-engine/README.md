# `services/reroute-engine/` — Capacity-Aware Re-Routing (THE CORE)

Proactive cascade-aware re-routing is the product's center of gravity, so its realism gaps are
**correctness, not polish** ([audit-01 §5](../../docs/audit-01-screening-feasibility.md),
[audit-03 §3](../../docs/audit-03-worth-winning-upgrades.md),
[audit-04 §7](../../docs/audit-04-flaws-edge-cases.md)).

## Modules (`cascadeguard_reroute/`)
| Module | Responsibility |
|---|---|
| `routing.py` | Deterministic alternative-train query (top-k candidates to the destination) |
| `ticketing.py` | Reserved-ticket **validity**, WL/Tatkal, live availability — **IRCTC mocked honestly** |
| `allocator.py` | **Capacity-constrained / congestion-game** assignment — spread fractionally, never herd |
| `feedback.py` | Close the loop: accepted re-routes feed back as demand |

## The guarantees that win the table
- Two passengers, same disruption → **different, feasible** routes (the 20-second proof).
- Never recommend a train at/over capacity; degrade to an honest "wait" ETA when nothing fits
  — which also prevents creating a *second* cascade onto the alternative.
- Surface ticket reality: a reserved ticket isn't valid on another train; show fresh-booking /
  Tatkal status rather than pretending you can just board.

## Implementation status (Stage 5, Steps 19–21 — done)
All four modules implemented and tested (`tests/`, run `pytest services/reroute-engine/tests`).

| Module | Status | Key API | Verified by |
|---|---|---|---|
| `routing.py` | ✅ | `find_alternatives(origin, dest, after_min, k)` → `Candidate`s from the twin timetable, sorted by earliest arrival | disrupted PNBE→BSB journey returns `[12303, 15049]` |
| `ticketing.py` | ✅ | `is_ticket_valid_on(orig, alt)` (train-specific); `live_availability(train)` → `Availability` (**mocked IRCTC**, deterministic) | reserved ticket invalid on an arbitrary alternative |
| `allocator.py` | ✅ | `allocate(passengers, candidates, capacity)` → capacity-weighted spread, no herding, honest `WAIT` when nothing fits | 2 passengers → different feasible routes; never exceeds seats |
| `feedback.py` | ✅ | `record_acceptance(pnr, train)` / `projected_demand(train)` — closes the demand loop | accepted re-route fills a seat → next passenger re-routed elsewhere |

Notes / honest mocks: platform numbers are mocked deterministically (real value comes from
COA/RTIS, where it is safety-critical); IRCTC availability is a deterministic stand-in.
Consumed next by the worker (Step 25) and the API `/reroute` endpoint (Step 26).
