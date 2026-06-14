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

## Implementation status (Stage 8, Step 28 — done)
Run: `npm run dev` → http://localhost:3001, with the API running. Typecheck: `npx tsc --noEmit`
(clean); `npm run build` produces `dist/` (~156 kB JS). API base via `VITE_API_BASE`
(default `http://localhost:8000`).

- `theme.ts` ✅ control-room dark tokens + `riskTone()` (green/amber/red, **grey = no/stale data**,
  never read as "safe") + the demo `CORRIDOR` (PNBE → MGS → BSB with display names).
- `styles.css` ✅ dark gradient backdrop, custom scrollbar, high-risk node pulse + fade-up keyframes.
- `lib/ws.ts` ✅ real `/ws/live` client: parses per-station **deltas** + the completion marker,
  auto-reconnects (keeps the corridor view live), returns a disposer. `lib/api.ts` ✅ `getCorridor`,
  `getStation` for the snapshot/drill-down reads.
- `main.tsx` ✅ shell: sticky header with brand, **live/connecting/offline** status, derived
  corridor-health chip (peak risk) + watermark; subscribes to the feed, keeps the per-station risk
  map, and fetches station snapshots on each completed sweep.
- `components/RiskHeatmap.tsx` ✅ the **line-diagram corridor** — nodes coloured by live risk, pulse
  when high, grey when stale, click to drive the drill-down. *(Self-contained SVG/CSS so it runs
  with zero config; a Mapbox GL layer keyed on the same per-station risk can drop in with a token —
  `mapbox-gl` is kept as a dependency for that geographic view.)*
- `components/CascadeChain.tsx` ✅ propagation path with per-hop risk %, delay window, and the
  GNNExplainer **why** (e.g. MGS `100% rake-link (12301→12302)`).
- `components/StationDrilldown.tsx` ✅ selected-station detail: risk, delay window, incoming
  at-risk trains, the why, and the staleness watermark.
- **Verify:** against a live API the WS streams MGS/PNBE/BSB at risk 0.89/0.89/0.87 → the corridor
  nodes turn **red live**; the chain shows the rake-link driver; the drill-down lists incoming trains.
