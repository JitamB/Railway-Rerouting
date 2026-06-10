# `services/notifier/` — Push Delivery + Cost-Sensitive Trigger

Decides **when** to alert and delivers the push.

## Modules (`cascadeguard_notify/`)
| Module | Responsibility |
|---|---|
| `trigger.py` | **Cost-sensitive / utility-based** trigger — notify when *expected passenger-minutes saved > expected false-alarm cost*, not a magic 65% ([audit-02 §4](../../docs/audit-02-architecture-deep-dive.md)) |
| `fcm.py` | Firebase Cloud Messaging delivery; works when the PWA is closed |

The trigger consumes the conformal interval (calibrated confidence) so the decision is made on
*known* uncertainty, not a point estimate. A fixed global threshold ignores that the cost of a
missed cascade varies by train/section.
