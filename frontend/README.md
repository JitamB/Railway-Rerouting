# `frontend/` — User Surfaces

| App | Role | Primacy |
|---|---|---|
| [passenger-app/](passenger-app/) | **Expo / React Native** native app (Android + iOS) — proactive re-route cards, helpline, background push | **PRIMARY** (this is the product) |
| [operator-dashboard/](operator-dashboard/) | React + Mapbox **web** — risk heatmap + cascade-chain visualisation | **Supporting context** |

The emphasis is deliberate ([audit-00](../docs/audit-00-verdict.md)): the passenger surface and
the "re-routed before the railway announced it" moment are the headline; the operator heatmap
is situational awareness, not the core. Lead demos with the app and the cascade graph, not the
dashboard.

**Why the split:** the passenger app is **native (Expo)** for reliable background push (the
core feature, unreliable on a web PWA — especially iOS) and microphone access for the helpline;
the operator dashboard stays **web** because operators work at a control-room desktop.

Both consume the API (`services/api/`): REST for queries, WebSocket (dashboard) for live deltas,
and `expo-notifications` (FCM/APNs) for passenger push.
