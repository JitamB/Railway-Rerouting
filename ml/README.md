# `ml/` — Prediction, Uncertainty, Explainability

The moat. **One** spatio-temporal GNN over the heterogeneous dependency graph — not the
v0 GNN+LSTM pair, which would disagree and create a consistency SPOF
([audit-02 §1.3](../docs/audit-02-architecture-deep-dive.md)).

## Why one ST-GNN
A cascade is space *and* time jointly. Workhorse: **Graph WaveNet** (learns the adjacency →
fixes hand-set weights) or **DCRNN** (diffusion ≈ cascade). The **graph-conditioned Hawkes /
neural point process** framing is the depth signal ([audit-03 §1](../docs/audit-03-worth-winning-upgrades.md)).

## Packages (`cascadeguard_ml/`)
| Path | Responsibility | Closes |
|---|---|---|
| `models/` | `stgnn.py` (ST-GNN), `hetero.py` (HeteroConv/RGCN), `layers.py` | audit-02 §3.3, audit-03 §1 |
| `training/` | `train.py`, `losses.py` (focal/cost-sensitive), `data_module.py` | audit-04 §6 |
| `uncertainty/` | `conformal.py` — distribution-free intervals + reliability curve | audit-03 §4 |
| `explain/` | `gnn_explainer.py` — per-cascade attribution ("why") | audit-03 §5 |
| `ood/` | `detector.py` — out-of-distribution flag → simulator fallback | audit-04 §2 |
| `eval/` | `calibration.py` (Brier/reliability), `ablation.py` (rake-link) | audit-02 §3.4, audit-04 §4 |
| `inference.py` | `python -m cascadeguard_ml.inference --station PNBE` | demo proof |

## The proof slide
**With-vs-without-rake-link ablation** (`eval/ablation.py`): show the topology edges
measurably improve cascade recall. Pair with the reliability curve and tail-recall metrics —
high overall accuracy is useless if the rare large cascades are missed
([audit-04 §6](../docs/audit-04-flaws-edge-cases.md)).

Configs in `configs/`; checkpoints in `checkpoints/` (git-ignored).
