from pathlib import Path

import pytest
import torch
import yaml

from cascadeguard_ml.models.stgnn import SpatioTemporalGNN
from cascadeguard_ml.spec import DEFAULT_CHECKPOINT, REPO_ROOT
from cascadeguard_ml.training.train import train

CONFIG = str(REPO_ROOT / "ml" / "configs" / "stgnn.example.yaml")


@pytest.fixture(scope="session")
def trained_model():
    """The trained ST-GNN artifact (train it once if missing)."""
    ckpt = DEFAULT_CHECKPOINT
    if not Path(ckpt).exists():
        train(CONFIG, ckpt)
    blob = torch.load(ckpt, map_location="cpu", weights_only=False)
    model = SpatioTemporalGNN(blob["config"])
    model.load_state_dict(blob["state_dict"])
    model.eval()
    return model
