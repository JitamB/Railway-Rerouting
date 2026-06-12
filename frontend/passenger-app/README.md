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
