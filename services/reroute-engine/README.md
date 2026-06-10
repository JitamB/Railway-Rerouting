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
