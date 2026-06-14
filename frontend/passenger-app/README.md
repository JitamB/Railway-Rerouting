# `frontend/passenger-app/` — Passenger App (Expo / React Native · PRIMARY surface)

A native **Android + iOS** app built with **Expo (React Native, TypeScript)** and **Expo
Router** (file-based navigation). This replaces the earlier Next.js PWA: a real app gives
**reliable background push** (the proactive re-route is the product) and proper **microphone
access** for the regional-language helpline — both weak spots for a web PWA, especially on iOS.

## Why Expo (vs PWA / bare RN / Flutter)
- **Background push that actually fires** via `expo-notifications` (FCM on Android, APNs on iOS)
  — a PWA can't guarantee this on iOS, and push *is* the headline feature.
- **Reuses the team's React/TypeScript** components and skills (Flutter would mean a Dart rewrite).
- **Hackathon-grade workflow:** Expo Go QR demo on a judge's phone, EAS Build, OTA updates —
  no Xcode/Android Studio babysitting. `expo prebuild` is the escape hatch if a native module is ever needed.

## Structure
| Path | Responsibility |
|---|---|
| `app/_layout.tsx` | Root tabs (Home · Helpline · My Queries); registers push on mount |
| `app/index.tsx` | Home — PNR registration + live status + the re-route card |
| `app/helpline.tsx` | Helpline — chat by text or regional-language speech |
| `app/queries.tsx` | My Queries — past queries + status (resolved/pending) |
| `components/RerouteCard.tsx` | Re-route card: delay, probability, feasible alternatives, seats, *why*, data-age |
| `components/HelplineChat.tsx` | Chat UI: text + mic; shows agent reply, case id, routed authority |
| `components/QueryHistory.tsx` | Past-query list with status badges + history drill-down |
| `lib/api.ts` | REST client to `services/api` (base URL from `app.json` → `extra.apiBaseUrl`) |
| `lib/push.ts` | `expo-notifications` registration + receipt handling |
| `lib/speech.ts` | `expo-av` mic capture → upload to `POST /helpline/chat` (server-side ASR) |
| `app.json` / `eas.json` | Expo + EAS build config (permissions, plugins, build profiles) |
| `assets/` | App icon / splash / notification icon (add the PNGs here) |

## Run / build
```bash
cd frontend/passenger-app
npm install
npx expo start            # scan the QR with Expo Go to run on a phone
# native builds:
npx eas build -p android  # or -p ios   (requires an Expo account)
```

## Notes
- **Backend is unchanged** — the app talks to the same FastAPI (`services/api`): REST for
  queries/re-route/helpline, `expo-notifications` for push. The **operator dashboard stays a web
  app** (control-room desktop use).
- Safety-critical fields (train no., platform, time) render from structured data, never LLM prose.
- Show the **staleness watermark** and **seat reality** (AVL/WL/Tatkal/FULL) — never imply you
  can just board a reserved train ([../../docs/problem-statement.md §7](../../docs/problem-statement.md)).
- Push needs `google-services.json` (Android/FCM) and an Expo push setup; keys live in the
  backend `.env` ([../../.env.example](../../.env.example)).

## Implementation status (Stage 8, Step 27 — done)
Run: `npx expo start` (scan with Expo Go) with the API running (`uvicorn cascadeguard_api.main:app`).
Typecheck: `npx tsc --noEmit` (clean). For a phone over the QR, set `app.json` →
`extra.apiBaseUrl` to your machine's LAN IP (not `localhost`).

- `lib/theme.ts` ✅ shared design tokens (colour, spacing, radius, shadow, type) + `riskStyle()` —
  the green/amber/red spine the whole UI keys on.
- `lib/api.ts` ✅ typed client mirroring `services/api`: `getCascade`, `getReroute`, `getQueries`,
  `postHelplineText`/`postHelplineAudio` (multipart). Tolerates the not-yet-built Stage-9 helpline.
- `app/_layout.tsx` ✅ branded icon tab bar (Home · Helpline · My Queries), registers push on mount.
- `app/index.tsx` ✅ Home: PNR registration → live `GET /cascade` + `POST /reroute`, pull-to-refresh,
  loading/error/empty states, foreground-push re-pull.
- `components/RerouteCard.tsx` ✅ the hero: risk meter + band, calibrated delay interval, the
  "why", capacity-checked alternatives with seat-reality badges (AVL/WL/FULL), a clearly-separated
  generated-guidance block, and the live/staleness watermark. Safety-critical fields render from
  structured data, never prose.
- `components/HelplineChat.tsx` ✅ chat bubbles, language chips (EN/हिं/বাং/தமி/తెల/मरा), text +
  on-device mic recording (`expo-audio`) → `POST /helpline/chat`, agent reply with case id +
  routed authority + status badge.
- `components/QueryHistory.tsx` ✅ case cards with status badges + empty state.
- `lib/push.ts` ✅ foreground handler + permission + Expo push token (dev/EAS build; Expo Go
  no-op). `lib/speech.ts` mic-permission helper (unchanged).
- **Verify:** typecheck clean; against a live API the Home card shows risk 87%, alternatives
  `12303`/`15049` with seats, and the "arrives BSB only 10 min later" guidance.
