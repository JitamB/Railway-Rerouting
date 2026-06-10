#!/usr/bin/env bash
# One-time dev setup (skeleton). Editable-installs each Python package and prepares env.
set -euo pipefail

cp -n .env.example .env || true

# Editable installs for local development.
for pkg in data/simulator data/ingestion data/graph ml \
           services/api services/reroute-engine services/llm-agent \
           services/notifier services/worker; do
  echo "pip install -e $pkg"
  # pip install -e "$pkg"
done

echo "Setup stub complete. Uncomment installs once dependencies are pinned."
