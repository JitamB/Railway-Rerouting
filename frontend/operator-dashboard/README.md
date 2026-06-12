# `frontend/operator-dashboard/` — Operator Dashboard (supporting context)

React + Mapbox GL JS (Vite). Station-level cascade-risk heatmap and cascade-chain visualisation
for situational awareness — **not** the core product (the passenger app is). Stays a **web** app
because operators work at a control-room desktop.

## Run (dev)
```bash
cd frontend/operator-dashboard
npm install
npm run dev        # http://localhost:3001
```
Currently a **skeleton shell**: it renders the dashboard layout with placeholder panels. The live
WebSocket feed needs `services/api` (implementation-guide Step 26) and the real Mapbox heatmap
needs a Mapbox token (Step 28). `npm run build` produces a production bundle in `dist/`.

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
