# `services/llm-agent/` — Claude Phrasing (template-first, async)

Converts raw model output into passenger-appropriate guidance. The LLM is for **communication**
(quality-critical, called sparingly), never **prediction** (speed-critical, runs locally) —
clear separation of concerns.

## Hard rules (from the audit)
- **Template-first, non-blocking** ([audit-02 §1.4](../../docs/audit-02-architecture-deep-dive.md)):
  the alert is emitted instantly from a deterministic template; Claude only *enriches* phrasing
  when reachable. The push never waits on the LLM, which keeps the "offline-capable" claim
  honest ([audit-02 §3.5](../../docs/audit-02-architecture-deep-dive.md)).
- **Safety-critical fields are templated, never generated** ([audit-04 bonus](../../docs/audit-04-flaws-edge-cases.md)):
  train number, platform, and time come from structured data; the LLM phrases only the prose.
  A mistranslated platform number is worse than no alert.

## Modules (`cascadeguard_llm/`)
| Module | Responsibility |
|---|---|
| `client.py` | Claude API client (`ANTHROPIC_MODEL`, default `claude-sonnet-4-6`) |
| `prompts.py` | Structured prompt: origin/dest, status, top-k alternatives, time sensitivity |
| `phrasing.py` | Async enrich; merges templated safety fields with LLM prose |
| `templates/` | Per (delay-band × language) canned guidance for the offline/degraded path |

Multilingual alerts (Hindi/Bengali/Tamil/Telugu/Marathi) are a prompt-engineering task on top —
but must be *verified*, with safety fields templated.
