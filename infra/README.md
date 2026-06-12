# `infra/` — Deployment & Operations

Everything to bring the stack up with one command and run the demo deterministically.

| Path | Role |
|---|---|
| `docker/` | Per-service build context helpers / shared base image bits |
| `redis/` | Redis Streams config (the store-and-forward buffer / event bus) |
| `db/init.sql` | PostgreSQL + **TimescaleDB** init: hypertables + continuous aggregates for delay events |
| `scripts/setup.sh` | One-time dev setup (editable installs, env, seed the twin) |
| `scripts/run_demo.sh` | Bring the stack up and replay a historical cascade on the twin |

Root `docker-compose.yml` wires `redis`, `timescaledb`, `api`, `worker`, `helpline`, and the
`operator-dashboard` web app. The **passenger app is native (Expo / React Native)** and is run
separately (`cd frontend/passenger-app && npx expo start` / EAS build), not containerized.
**On stage, run the twin — never depend on the live network**
([audit-03 §9](../docs/audit-03-worth-winning-upgrades.md)).
