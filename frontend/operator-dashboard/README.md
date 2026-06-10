# `frontend/operator-dashboard/` — Operator Dashboard (supporting context)

React + Mapbox GL JS. Station-level cascade-risk heatmap and cascade-chain visualisation for
situational awareness — **not** the core product (the passenger PWA is).

## Key pieces (`src/`)
| Path | Responsibility |
|---|---|
| `main.tsx` | App entry; connects the WebSocket live feed |
| `components/RiskHeatmap.tsx` | Colour-coded station nodes (green→amber→red), updated by WS deltas |
| `components/CascadeChain.tsx` | "Train 12301 → Patna Jn → Mughal Sarai (71%) → Varanasi (54%)…" with the *why* per hop |
| `components/StationDrilldown.tsx` | Per-station: at-risk trains + estimated new arrival windows |
| `lib/ws.ts` | WebSocket client for `/ws/live` (consumes deltas, not full state) |

Predictions display their **staleness watermark** and grey out when stale ([audit-04 §1](../../docs/audit-04-flaws-edge-cases.md)).
Phase-2 may add an operator decision layer (hold/precedence/platform) on top — off the critical
path ([audit-03 §7](../../docs/audit-03-worth-winning-upgrades.md)).
