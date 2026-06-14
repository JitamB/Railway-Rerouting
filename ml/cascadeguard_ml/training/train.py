"""Training entrypoint for the spatio-temporal GNN.

Fits the model + the learned edge-type gates end-to-end with a tail-aware objective (focal on
cascade risk + cost-sensitive Huber on delay). Writes a checkpoint to ``ml/checkpoints/``.
Run: ``python -m cascadeguard_ml.training.train --config ml/configs/stgnn.example.yaml``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
import yaml

from cascadeguard_ml.models.stgnn import SpatioTemporalGNN
from cascadeguard_ml.spec import DEFAULT_CHECKPOINT
from cascadeguard_ml.training.data_module import CascadeDataModule
from cascadeguard_ml.training.losses import cost_sensitive_loss, focal_loss


def _loss(out, batch, miss_cost: float, delay_weight: float):
    y = batch["service"]
    risk = focal_loss(out["risk_logit"], y.y_risk)
    delay = cost_sensitive_loss(out["delay"], y.y_delay, miss_cost=miss_cost)
    return risk + delay_weight * delay


@torch.no_grad()
def _val_loss(model, loader, miss_cost, delay_weight) -> float:
    model.eval()
    total, n = 0.0, 0
    for batch in loader:
        total += float(_loss(model(batch), batch, miss_cost, delay_weight))
        n += 1
    return total / max(n, 1)


def fit(model, dm, tr: dict, verbose: bool = True):
    """Fit a model on a datamodule with the tail-aware objective. Returns the model."""
    opt = torch.optim.Adam(model.parameters(), lr=tr.get("lr", 0.005))
    epochs = tr.get("epochs", 40)
    bs = tr.get("batch_size", 32)
    miss_cost = tr.get("miss_cost", 10.0)
    delay_weight = tr.get("delay_weight", 0.5)
    if verbose:
        print(f"training ST-GNN ({sum(p.numel() for p in model.parameters())} params) "
              f"on {len(dm._train)} samples, {epochs} epochs")
    for epoch in range(1, epochs + 1):
        model.train()
        for batch in dm.train_dataloader(batch_size=bs):
            opt.zero_grad()
            loss = _loss(model(batch), batch, miss_cost, delay_weight)
            loss.backward()
            opt.step()
        if verbose and (epoch == 1 or epoch % 5 == 0 or epoch == epochs):
            print(f"  epoch {epoch:>3}  train {loss.item():.4f}  "
                  f"val {_val_loss(model, dm.val_dataloader(bs), miss_cost, delay_weight):.4f}")
    return model


def train(config_path: str, checkpoint: str = DEFAULT_CHECKPOINT) -> str:
    """Load config, build datamodule + model, fit, checkpoint. Returns the checkpoint path."""
    cfg = yaml.safe_load(Path(config_path).read_text())
    tr = cfg.get("training", {})
    torch.manual_seed(tr.get("seed", 0))

    dm = CascadeDataModule(n_samples=tr.get("n_samples", 256), seed=tr.get("seed", 0))
    model = fit(SpatioTemporalGNN(cfg), dm, tr)

    Path(checkpoint).parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "config": cfg}, checkpoint)
    print(f"saved checkpoint -> {checkpoint}")
    return checkpoint


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the CascadeGuard ST-GNN.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
    args = parser.parse_args()
    train(args.config, args.checkpoint)


if __name__ == "__main__":
    main()
