#!/usr/bin/env bash
# Cold demo replay — the full vertical slice on the digital twin, with the cable unplugged.
# No Docker, no live network, no API keys. Target: < 4 minutes end to end.
#
#   bash infra/scripts/run_demo.sh
set -euo pipefail

cd "$(dirname "$0")/../.."   # repo root
# shellcheck disable=SC1091
source .venv/bin/activate

section() { printf '\n\033[1;36m━━ %s ━━\033[0m\n' "$1"; }

# Train the ST-GNN if the checkpoint is missing (build artifact, not in git) — keeps the demo
# self-sufficient even if setup.sh wasn't run first.
[ -f ml/checkpoints/stgnn.pt ] || \
  python -m cascadeguard_ml.training.train --config ml/configs/stgnn.example.yaml

START=$(date +%s)

section "1/6 · Contracts locked"
python shared/validate.py

section "2/6 · Digital twin (OHE failure at MGS)"
python data/simulator/run_twin.py --scenario ohe_failure --horizon 160

section "3/6 · ST-GNN cascade forecast (runs locally on the twin)"
python -m cascadeguard_ml.inference --station MGS

section "4/6 · Worker pipeline — a twin delay flows all the way to a push"
python services/worker/run_pipeline.py --scenario ohe_failure --station MGS

section "5/6 · Helpline — spoken regional-language grievance → routed, tracked case"
python - <<'PY'
from cascadeguard_helpline.agent import HelplineAgent
from cascadeguard_helpline.cases import list_cases
agent = HelplineAgent()
for utterance, lang in [("B4 coach mein ek lawaris bag pada hai", "hi"),
                        ("please process my refund / TDR", "en")]:
    r = agent.handle("demo_pax", audio=utterance.encode(), language=lang)
    print(f"  🎤 [{lang}] {utterance}\n     → {r.case_id} · {r.authority} · {r.status}")
print("  My Queries:", [f"{c.case_id}:{c.status.value}" for c in list_cases("demo_pax")])
PY

section "6/6 · End-to-end demo scenarios (offline)"
python -m pytest tests/e2e -q

END=$(date +%s)
printf '\n\033[1;32m✓ Demo complete in %ss (no live network used).\033[0m\n' "$((END - START))"
cat <<'EOF'

Proof slide (separate, retrains 2 models — ~minutes):
  python -m cascadeguard_ml.eval.ablation     # rake-link lifts tail recall 0.50 → 1.00

Live surfaces (optional, need the API up):
  uvicorn cascadeguard_api.main:app --reload
  cd frontend/operator-dashboard && npm run dev    # inject a delay → corridor lights up red
  cd frontend/passenger-app && npx expo start
EOF
