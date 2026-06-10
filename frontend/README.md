# `frontend/` — User Surfaces

| App | Role | Primacy |
|---|---|---|
| [passenger-pwa/](passenger-pwa/) | Next.js PWA + FCM — proactive re-route cards, offline-first, installable | **PRIMARY** (this is the product) |
| [operator-dashboard/](operator-dashboard/) | React + Mapbox — risk heatmap + cascade-chain visualisation | **Supporting context** |

The emphasis is deliberate ([audit-00](../docs/audit-00-verdict.md)): the passenger surface and
the "re-routed before the railway announced it" moment are the headline; the operator heatmap
is situational awareness, not the core. Lead demos with the PWA and the cascade graph, not the
dashboard.

Both consume the API (`services/api/`): REST for queries, WebSocket for live deltas, FCM for
push.
