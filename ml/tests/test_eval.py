import numpy as np
import yaml

from cascadeguard_ml.eval.ablation import run_ablation
from cascadeguard_ml.eval.calibration import brier_score, drift_flag, reliability_curve


def test_brier_score():
    # perfect confident-correct predictions -> Brier 0
    assert brier_score([1.0, 0.0, 1.0], [1, 0, 1]) == 0.0
    # confident-wrong -> Brier 1
    assert brier_score([0.0, 1.0], [1, 0]) == 1.0


def test_reliability_curve_diagonal_for_calibrated():
    rng = np.random.default_rng(0)
    probs = rng.uniform(0, 1, 5000)
    outcomes = (rng.uniform(0, 1, 5000) < probs).astype(int)  # perfectly calibrated by construction
    pred, obs, _ = reliability_curve(probs, outcomes, bins=10)
    assert np.allclose(pred, obs, atol=0.08)  # observed tracks predicted along the diagonal


def test_drift_flag():
    stable = [0.1] * 4000
    assert drift_flag(stable, window=1000) is False
    degrading = [0.1] * 2000 + [0.5] * 1000  # recent window much worse
    assert drift_flag(degrading, window=1000) is True


def test_ablation_rake_link_lifts_tail_recall(tmp_path):
    cfg = {
        "model": {"hidden_dim": 32, "layers": 3, "arch": "graph_wavenet"},
        "training": {"epochs": 30, "lr": 0.01, "batch_size": 32, "n_samples": 160,
                     "miss_cost": 10.0, "delay_weight": 1.0, "seed": 0},
    }
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))

    results = {r.variant: r for r in run_ablation(str(cfg_path))}
    # the topology edge measurably lifts tail recall — the proof slide
    assert results["with_rake_link"].tail_recall > results["without_rake_link"].tail_recall
