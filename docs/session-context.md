# Session Context — Handoff for Implementation

Brief context to resume work in a new chat. The build plan itself is in
[implementation-guide.md](implementation-guide.md); this file is the surrounding state.

## What this project is
**CascadeGuard** — real-time delay-cascade predictor + proactive passenger re-routing for
Indian Railways. Authoritative spec: [problem-statement.md](problem-statement.md). Runtime +
build sequence: [workflow.md](workflow.md). Architecture follows the **hardened audit version**
(digital-twin primary data, ONE spatio-temporal GNN over a heterogeneous graph, capacity-aware
re-routing, helpline grievance subsystem, template-first/async LLM).

## Current repo state
- **Fully scaffolded skeleton.** Every file exists; Python packages are stubs (signatures +
  `...`), JSON/manifests are real. Nothing in the backend/ML/data layers is implemented yet.
- **Both frontends actually run** (placeholder UI):
  - `frontend/passenger-app/` — **Expo / React Native, SDK 54** (primary surface). Runs in
    Expo Go: `cd frontend/passenger-app && npx expo start -c`. Tabs: Home / Helpline / My Queries.
  - `frontend/operator-dashboard/` — **Vite + React** (web, context). `npm run dev` → http://localhost:3001.
- Backend/data/ml = stubs awaiting implementation per the guide.

## Where to start
Open [implementation-guide.md](implementation-guide.md) and begin at **Step 1** (lock the
`shared/schemas` contracts) → **Step 2** (infra: Redis + TimescaleDB) → Stage 1 digital twin,
etc. The guide is dependency-ordered: each step says what it inherits and what it feeds next,
with a `Verify:` check. 🎯 markers are points where something is runnable/demoable.

## Environment setup (gotchas already solved — don't rediscover)
- **Python → use `.venv` (Python 3.11.7), never conda `base`.** Base resolves to Homebrew
  Python **3.14** (too new for torch/PyG). Activate cleanly:
  ```bash
  conda deactivate && source .venv/bin/activate    # prompt: (.venv) only
  ```
  Then `pip install -e ml` etc. (one shared venv for all `cascadeguard_*` packages — they
  import each other). Avoid the stacked `(.venv) (base)` prompt.
- **Node is v25** (bleeding-edge, unsupported by Vite/Expo). Everything works, but if you hit
  weird dev-server/build errors, switch to **Node 20 LTS** (`nvm use 20`) first.
- **Watchman** is installed (fixes Metro `EMFILE: too many open files`).
- **Docker Desktop** is installed; if `docker` is "command not found", open a **fresh terminal**
  (its PATH symlink was added mid-session). `docker compose config` already validates.

## Frontend specifics
- **Push**: real background push is a **no-op in Expo Go by design** (removed from Expo Go in
  SDK 53). `lib/push.ts` guards for Expo Go and lazy-imports `expo-notifications`. Real push
  needs a **dev build** (`npx expo run:android` or EAS).
- **Audio**: migrated `expo-av` → **`expo-audio`** (expo-av is deprecated). Recording will use
  the `useAudioRecorder` hook in `HelplineChat`.
- **Operator dashboard** renders a placeholder shell; real Mapbox heatmap + WS live feed come
  at guide **Steps 26 & 28** (need `services/api` + a Mapbox token).

## Git state
- Branch `main`. Last commit: `9f64279`. History has the scaffold + helpline + Expo migration +
  dashboard + this guide, committed in themed/per-file commits (no co-author tag).
- **Uncommitted** (the Expo Go push fix + expo-audio migration):
  `frontend/passenger-app/{app.json, package.json, package-lock.json, lib/push.ts, lib/speech.ts, components/HelplineChat.tsx}`.
  Suggested commits: "Guard push for Expo Go (lazy import)" + "Migrate expo-av → expo-audio".
- **Stray to ignore/delete**: root `./package-lock.json` (6 lines, no root `package.json`) — junk
  from an accidental root `npm install`; do not commit. `rm package-lock.json` is safe.

## Conventions to keep
- Twin-first (nothing on stage depends on a live feed). Mock COA/RTIS, IRCTC, Bhashini,
  RailMadad honestly behind clean adapters. Structured fields authoritative; LLM only phrases.
- Per repo `CLAUDE.md`: minimal/surgical changes, simplicity first, ask when ambiguous.
