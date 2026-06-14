import math

import torch
import yaml

from cascadeguard_ml.models.stgnn import SpatioTemporalGNN
from cascadeguard_ml.training.losses import cost_sensitive_loss, focal_loss
from cascadeguard_ml.training.train import train


def test_focal_and_cost_sensitive_losses():
    logits = torch.tensor([2.0, -2.0, 0.5])
    target = torch.tensor([1.0, 0.0, 1.0])
    fl = focal_loss(logits, target)
    assert fl.item() > 0 and torch.isfinite(fl)

    # a tail target underpredicted costs much more than an ordinary one
    big_miss = cost_sensitive_loss(torch.tensor([0.0]), torch.tensor([30.0]), miss_cost=10.0)
    small_miss = cost_sensitive_loss(torch.tensor([0.0]), torch.tensor([5.0]), miss_cost=10.0)
    assert big_miss > small_miss


def test_train_saves_loadable_checkpoint(tmp_path):
    cfg = {
        "model": {"hidden_dim": 16, "layers": 2, "arch": "graph_wavenet"},
        "training": {"epochs": 3, "lr": 0.01, "batch_size": 16, "n_samples": 32,
                     "miss_cost": 10.0, "delay_weight": 0.1, "seed": 0},
    }
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))
    ckpt = tmp_path / "stgnn.pt"

    train(str(cfg_path), str(ckpt))
    assert ckpt.exists()

    # the checkpoint reloads into a fresh model
    model = SpatioTemporalGNN(cfg).load(str(ckpt))
    assert isinstance(model, SpatioTemporalGNN)
