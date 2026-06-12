#!/usr/bin/env bash
# Bring the stack up and replay a historical cascade on the digital twin (skeleton).
# On stage: run the twin, never the live network (audit-03 §9).
set -euo pipefail

docker compose up -d redis timescaledb
# python -m cascadeguard_sim.engine --config data/simulator/config/section.example.yaml --replay <event>
# python -m cascadeguard_worker.pipeline &
# docker compose up -d api operator-dashboard   # passenger app is native: cd frontend/passenger-app && npx expo start

echo "Demo stub: wire the twin replay + worker once Phase 1-4 land."
