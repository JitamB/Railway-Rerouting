"""The single best proof slide: with-vs-without-rake-link ablation (audit-02 §3.4).

Trains/evaluates the model with and without the rake-link edge type and reports the delta on
**tail recall** (large-cascade events), proving the topology edges measurably matter rather
than just being decoration.

Two design points that keep the comparison honest and decisive:
  * **Recall at a fixed false-alarm rate.** Plain recall is gameable — the tail-aware loss
    pushes both models to over-alert, maxing recall. We instead pick each model's threshold so
    its false-alarm rate on non-tail events is equal, then measure tail recall. That rewards
    *discrimination*, which is what the topology buys.
  * **Closures-only (regime held fixed).** Both variants see identical targets (the twin always
    has the real rake turnaround physics); only the graph edge differs. We disable fog so the
    outbound's delay is *purely* rake-driven — otherwise the regime feature leaks a shortcut.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
import yaml

from cascadeguard_ml.eval.calibration import brier_score
from cascadeguard_ml.models.stgnn import SpatioTemporalGNN
from cascadeguard_ml.spec import TAIL_THRESHOLD
from cascadeguard_ml.training.data_module import CascadeDataModule
from cascadeguard_ml.training.train import fit

FALSE_ALARM_BUDGET = 0.15  # operating point: equal false-alarm rate on non-tail events


@dataclass
class AblationResult:
    variant: str           # "with_rake_link" | "without_rake_link"
    tail_recall: float     # recall on tail cascades at a fixed false-alarm rate
    brier: float


def _recall_at_fixed_fpr(score: np.ndarray, tail: np.ndarray, budget: float) -> float:
    nontail = score[~tail]
    if tail.sum() == 0 or len(nontail) == 0:
        return float("nan")
    threshold = float(np.quantile(nontail, 1.0 - budget))  # allow `budget` false alarms
    return float((score[tail] > threshold).mean())


@torch.no_grad()
def _evaluate(model, dm) -> tuple[float, float]:
    model.eval()
    pred_delay, act_delay, probs, risk = [], [], [], []
    for batch in dm.test_dataloader():
        out = model(batch)
        pred_delay.append(out["delay"])
        act_delay.append(batch["service"].y_delay)
        probs.append(torch.sigmoid(out["risk_logit"]))
        risk.append(batch["service"].y_risk)
    pd = torch.cat(pred_delay).numpy()
    tail = torch.cat(act_delay).numpy() > TAIL_THRESHOLD
    recall = _recall_at_fixed_fpr(pd, tail, FALSE_ALARM_BUDGET)
    return recall, brier_score(torch.cat(probs).numpy(), torch.cat(risk).numpy())


def run_ablation(config_path: str) -> list[AblationResult]:
    """Run both variants and return their tail-recall / Brier metrics for comparison."""
    cfg = yaml.safe_load(open(config_path))
    tr = cfg.get("training", {})
    seed = tr.get("seed", 0)
    n = tr.get("n_samples", 256)

    results = []
    for variant, ablate in [("with_rake_link", False), ("without_rake_link", True)]:
        torch.manual_seed(seed)
        dm = CascadeDataModule(n_samples=n, seed=seed, ablate_rake_link=ablate, fog_prob=0.0)
        model = fit(SpatioTemporalGNN(cfg), dm, tr, verbose=False)
        recall, brier = _evaluate(model, dm)
        results.append(AblationResult(variant, recall, brier))
    return results


def main() -> None:
    import argparse

    from cascadeguard_ml.spec import REPO_ROOT

    ap = argparse.ArgumentParser(description="Rake-link ablation (the proof slide).")
    ap.add_argument("--config", default=str(REPO_ROOT / "ml" / "configs" / "stgnn.example.yaml"))
    args = ap.parse_args()

    results = {r.variant: r for r in run_ablation(args.config)}
    print(f"\n{'variant':<22}{'tail recall':>14}{'brier':>10}")
    print("-" * 46)
    for variant in ("without_rake_link", "with_rake_link"):
        r = results[variant]
        print(f"{r.variant:<22}{r.tail_recall:>14.2f}{r.brier:>10.3f}")
    lift = results["with_rake_link"].tail_recall - results["without_rake_link"].tail_recall
    print(f"\nrake-link lifts tail recall by {lift:+.2f} "
          f"({results['without_rake_link'].tail_recall:.2f} → {results['with_rake_link'].tail_recall:.2f})\n")


if __name__ == "__main__":
    main()
