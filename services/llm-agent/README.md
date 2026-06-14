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
| `client.py` | LLM client — Groq, OpenAI-compatible (`GROQ_MODEL`, default `llama-3.1-8b-instant`) |
| `prompts.py` | Structured prompt: origin/dest, status, top-k alternatives, time sensitivity |
| `phrasing.py` | Async enrich; merges templated safety fields with LLM prose |
| `templates/` | Per (delay-band × language) canned guidance for the offline/degraded path |

Multilingual alerts (Hindi/Bengali/Tamil/Telugu/Marathi) are a prompt-engineering task on top —
but must be *verified*, with safety fields templated.

## Implementation status (Stage 6, Step 23 — done)
Test: `pytest services/llm-agent/tests`.

- `client.py` ✅ `LlmClient.phrase()` — async `AsyncGroq` chat-completion, model `GROQ_MODEL`
  (default `llama-3.1-8b-instant`), lazy client (imports without a key); raises when unreachable so
  the caller falls back. A short rephrase, not a reasoning task — a small/fast model is plenty.
  Provider-swappable: any OpenAI-compatible endpoint (OpenAI, Together, local Ollama/vLLM) works
  by changing this one file.
- `prompts.py` ✅ `build_guidance_prompt(...)` — structured facts + capacity-checked alternatives;
  instructs the model to keep every number exactly.
- `phrasing.py` ✅ `render_template(band, language, fields)` (instant, offline-safe) +
  `enrich(template_text, prompt, client, safety_fields=)` — upgrades prose when Claude is
  reachable, **falls back to the template on any failure**, and rejects LLM output that dropped a
  safety-critical field (so train no./platform/time are always the templated ones).
- `templates/en.delay-bands.txt` ✅ low/medium/high bands; unknown language falls back to English.
