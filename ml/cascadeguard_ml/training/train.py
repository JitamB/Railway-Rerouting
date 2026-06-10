"""Training entrypoint for the spatio-temporal GNN.

Fits the model + the learned edge weights end-to-end with a tail-aware objective. Writes a
checkpoint to ``ml/checkpoints/``. Run: ``python -m cascadeguard_ml.training.train --config ml/configs/stgnn.example.yaml``.
"""

from __future__ import annotations

import argparse


def train(config_path: str) -> None:
    """Load config, build datamodule + model, fit, checkpoint."""
    ...


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the CascadeGuard ST-GNN.")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    train(args.config)


if __name__ == "__main__":
    main()
