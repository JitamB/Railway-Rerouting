# `services/notifier/` — Push Delivery + Cost-Sensitive Trigger

Decides **when** to alert and delivers the push.

## Modules (`cascadeguard_notify/`)
| Module | Responsibility |
|---|---|
| `trigger.py` | **Cost-sensitive / utility-based** trigger — notify when *expected passenger-minutes saved > expected false-alarm cost*, not a magic 65% ([audit-02 §4](../../docs/audit-02-architecture-deep-dive.md)) |
| `fcm.py` | Push delivery via `expo-notifications` (FCM on Android, APNs on iOS); works when the app is closed |

The trigger consumes the conformal interval (calibrated confidence) so the decision is made on
*known* uncertainty, not a point estimate. A fixed global threshold ignores that the cost of a
missed cascade varies by train/section.

## Implementation status (Stage 6, Steps 22 & 24 — done)
Test: `pytest services/notifier/tests`.

- `trigger.py` ✅ `should_notify(risk, interval_min, minutes_saved_est, false_alarm_cost)` — fires
  iff `risk · confidence · minutes_saved > (1-risk) · false_alarm_cost`, where `confidence = lo/hi`
  of the conformal interval (a low-confidence small delay has `lo≈0` → won't fire; a confident
  large cascade fires).
- `fcm.py` ✅ `FcmSender.send(token, title, body, data)` — real firebase-admin path (lazy import)
  when `FCM_PROJECT_ID` + `FCM_CREDENTIALS_JSON` are set; otherwise an **honest mock** that returns
  a `mock-fcm-…` id so the demo runs without Firebase. Delivery never waits on the LLM.
