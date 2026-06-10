# `frontend/passenger-pwa/` — Passenger PWA (PRIMARY surface)

Next.js Progressive Web App. The passenger registers their active PNR; the system pushes a
**proactive re-route** when cascade risk crosses the cost-sensitive trigger — before the
official delay is announced.

## Key pieces (`src/`)
| Path | Responsibility |
|---|---|
| `app/page.tsx` | PNR registration + the live status / re-route view |
| `app/helpline/page.tsx` | **Helpline** — chat with the support agent by text or regional-language speech |
| `app/queries/page.tsx` | **My Queries** — past queries + their status (resolved/pending) |
| `components/RerouteCard.tsx` | The re-route card: current delay, probability, 1-3 **feasible** alternatives with platform/time/seats, and a one-line *why* |
| `components/HelplineChat.tsx` | Chat UI: text input + mic for speech; shows the agent reply, opened case id, and routed authority |
| `components/QueryHistory.tsx` | Past-query list with status badges; drill into a case's history |
| `lib/push.ts` | FCM registration + service-worker push handling (works app-closed) |
| `lib/speech.ts` | Microphone capture (MediaRecorder); audio is transcribed server-side by the helpline ASR |
| `public/manifest.json` | PWA manifest (installable, offline-first) |

## Helpline (grievance) flow
Speak/type → `POST /helpline/chat` → agent transcribes (regional-language ASR), understands the
query, fetches the passenger's details, opens a tracked case, and routes it to the right
authority. The reply names the case id + department; the case then appears under **My Queries**
with a live status. Backed by [`services/helpline`](../../services/helpline/README.md).

## Honesty in the UI
- Show the **staleness watermark** ("based on data N s old"); grey out when stale ([audit-04 §1](../../docs/audit-04-flaws-edge-cases.md)).
- Show **seat reality** (AVL/WL/Tatkal/FULL) — never imply you can just board a reserved train ([audit-01 §5](../../docs/audit-01-screening-feasibility.md)).
- Safety-critical fields (train no., platform, time) render from structured data, not LLM prose.
