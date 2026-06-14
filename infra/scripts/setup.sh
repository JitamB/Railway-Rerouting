#!/usr/bin/env bash
# One-time dev setup. Creates a Python 3.11 venv and editable-installs every package into it,
# then copies the env template. Idempotent — safe to re-run. Frontend installs are optional
# (pass --frontends) since they pull large node_modules.
set -euo pipefail

cd "$(dirname "$0")/../.."   # repo root

PY="${PYTHON:-python3.11}"
command -v "$PY" >/dev/null 2>&1 || PY="python3"

if [ ! -d .venv ]; then
  echo "==> creating .venv ($PY)"
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip -q

# Editable installs. ml pulls torch + torch-geometric (the heavy one). notifier installs without
# deps because firebase-admin is large and FCM is mocked + lazy-imported.
PKGS=(data/simulator data/ingestion data/graph ml \
      services/reroute-engine services/llm-agent services/api \
      services/worker services/helpline)
for pkg in "${PKGS[@]}"; do
  echo "==> pip install -e $pkg"
  pip install -e "$pkg" -q
done
echo "==> pip install -e services/notifier --no-deps"
pip install -e services/notifier --no-deps -q

cp -n .env.example .env 2>/dev/null && echo "==> wrote .env from .env.example" || true

# Train the ST-GNN once if the checkpoint is missing (it's a build artifact, not in git).
if [ ! -f ml/checkpoints/stgnn.pt ]; then
  echo "==> training the ST-GNN (one-time; ~1-2 min)"
  python -m cascadeguard_ml.training.train --config ml/configs/stgnn.example.yaml
fi

if [ "${1:-}" = "--frontends" ]; then
  echo "==> installing frontend deps (this is slow)"
  (cd frontend/passenger-app && npm install)
  (cd frontend/operator-dashboard && npm install)
fi

echo "==> verifying contracts"
python shared/validate.py

cat <<'EOF'

Setup complete. Next:
  source .venv/bin/activate
  bash infra/scripts/run_demo.sh          # offline demo arc + e2e (no live network)

Live surfaces (optional):
  uvicorn cascadeguard_api.main:app --reload          # REST + WS  (services/api)
  cd frontend/operator-dashboard && npm run dev        # dashboard  :3001
  cd frontend/passenger-app && npx expo start          # passenger app (Expo Go)
EOF
