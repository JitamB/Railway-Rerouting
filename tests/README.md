# `tests/` — Cross-Service Integration / E2E

Per-package unit tests live next to their code (`*/tests/`). This directory holds tests that
span services — the ones that prove the *demo* works end to end.

| Path | Covers |
|---|---|
| `e2e/` | Twin event → ingestion/validation → ST-GNN → re-route → alert (the full pipeline) |

## Priority scenarios (the demo-critical ones)
- **Replay a historical cascade** on the twin and assert downstream stations light up before
  they fail.
- **Two passengers, same disruption → different, feasible re-routes** (no herding, capacity
  respected) — [audit-04 §7](../docs/audit-04-flaws-edge-cases.md).
- **Kill the feed → graceful degradation** (live → dead-reckoning → schedule-prior), with the
  staleness watermark present and no silent blankness — [audit-04 §1](../docs/audit-04-flaws-edge-cases.md).
- **Inject a teleporting GPS fix → validation gate quarantines it** (no phantom cascade) —
  [audit-04 §3/§8](../docs/audit-04-flaws-edge-cases.md).
