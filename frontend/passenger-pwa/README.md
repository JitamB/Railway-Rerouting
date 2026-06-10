# `frontend/passenger-pwa/` — Passenger PWA (PRIMARY surface)

Next.js Progressive Web App. The passenger registers their active PNR; the system pushes a
**proactive re-route** when cascade risk crosses the cost-sensitive trigger — before the
official delay is announced.

## Key pieces (`src/`)
| Path | Responsibility |
|---|---|
| `app/page.tsx` | PNR registration + the live status / re-route view |
| `components/RerouteCard.tsx` | The re-route card: current delay, probability, 1-3 **feasible** alternatives with platform/time/seats, and a one-line *why* |
| `lib/push.ts` | FCM registration + service-worker push handling (works app-closed) |
| `public/manifest.json` | PWA manifest (installable, offline-first) |

## Honesty in the UI
- Show the **staleness watermark** ("based on data N s old"); grey out when stale ([audit-04 §1](../../docs/audit-04-flaws-edge-cases.md)).
- Show **seat reality** (AVL/WL/Tatkal/FULL) — never imply you can just board a reserved train ([audit-01 §5](../../docs/audit-01-screening-feasibility.md)).
- Safety-critical fields (train no., platform, time) render from structured data, not LLM prose.
