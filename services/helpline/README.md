# `services/helpline/` — Passenger Helpline & Grievance Redressal

The conversational support subsystem. A passenger opens the helpline, asks a question or files
a grievance by **text or regional-language speech**; an **agent** understands the query,
fetches the passenger's details, opens a tracked **case**, and forwards it to the **appropriate
authority** (RailMadad-style routing). The passenger can later see every past query and its
status.

This is a distinct bounded context from the cascade/re-route pipeline. It reuses the project's
principles: **structured fields are authoritative, the LLM only phrases**; **mock external
systems honestly and design the real adapter**; **PII is minimized and consented**.

## Modules (`cascadeguard_helpline/`)
| Module | Responsibility |
|---|---|
| `agent.py` | Orchestrator — runs the steps: transcribe → understand → fetch details → open case → route → dispatch → reply |
| `asr.py` | Speech-to-text for regional languages (Bhashini/ULCA primary, Whisper fallback) |
| `tts.py` | Text-to-speech for spoken replies in the passenger's language (optional, bidirectional) |
| `intent.py` | Intent classification + entity extraction (PNR, train, station, complaint category) |
| `passenger.py` | Fetch passenger details from PNR/profile (reuses ticketing mock + profile store) |
| `authorities.py` | Authority/department registry (config-backed) |
| `authority_router.py` | Map a classified grievance → the correct authority |
| `cases.py` | Case lifecycle + history: `open → in_progress → resolved` (and `rejected`) |
| `dispatch.py` | Send the case to the authority over a channel (RailMadad API / email — mocked) |

Config: `config/authorities.example.yaml`. The agent is exposed to the app through the API
(`services/api` routers `helpline` and `queries`).

## Language support
- **Input:** text + speech. Speech → `asr.py` (regional Indian languages); query may be
  machine-translated to a working language for the agent, then replies translated back.
- **Output:** text always; optional `tts.py` spoken reply in the same language.
- Bhashini (ULCA) is the India-credible default for ASR/NMT/TTS; not openly turnkey for all
  pairs, so it is **mocked honestly** with a clean adapter, Whisper as an offline fallback.

## Safety & privacy
- The **dispatched case carries structured fields** (category, PNR, train, location); the LLM
  phrases only the human-readable summary — a misrouted department is worse than a clumsy
  sentence.
- Grievances are PII. Store the **minimum** needed for status tracking, scope each passenger
  to their own queries, and honour a retention policy ([../../docs/audit-04-flaws-edge-cases.md](../../docs/audit-04-flaws-edge-cases.md) bonus: privacy).
