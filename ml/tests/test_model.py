import torch

from cascadeguard_ml.models.layers import DiffusionConv
from cascadeguard_ml.models.stgnn import NodePrediction, SpatioTemporalGNN
from cascadeguard_ml.training.data_module import CascadeDataModule

CONFIG = {"model": {"hidden_dim": 32, "layers": 3, "arch": "graph_wavenet"}}


def _batch_and_model():
    dm = CascadeDataModule(n_samples=16, seed=5)
    batch = next(iter(dm.train_dataloader(batch_size=4)))
    return dm, batch, SpatioTemporalGNN(CONFIG)


def test_forward_returns_right_shapes():
    dm, batch, model = _batch_and_model()
    out = model(batch)
    n_service = batch["service"].x.size(0)
    assert out["risk_logit"].shape == (n_service,)
    assert out["delay"].shape == (n_service,)
    assert out["embedding"].shape == (n_service, model.hidden)


def test_predict_returns_node_predictions():
    dm = CascadeDataModule(n_samples=4, seed=6)
    sample = dm.demo_sample("MGS")
    model = SpatioTemporalGNN(CONFIG)
    names = [n.split(":", 1)[1] for n in sorted(dm.sv_idx, key=lambda k: dm.sv_idx[k])]
    preds = model.predict(sample, names)
    assert len(preds) == 4
    assert all(isinstance(p, NodePrediction) for p in preds)
    assert all(0.0 <= p.cascade_risk <= 1.0 for p in preds)
    assert all(len(p.delay_interval_min) == 2 for p in preds)


def test_backward_pass_updates_params():
    dm, batch, model = _batch_and_model()
    out = model(batch)
    loss = out["risk_logit"].pow(2).mean() + out["delay"].pow(2).mean()
    loss.backward()
    with_grad = [(n, p) for n, p in model.named_parameters() if p.grad is not None]
    assert with_grad
    assert all(torch.isfinite(p.grad).all() for _, p in with_grad)
    names = {n for n, _ in with_grad}
    # the service-side path trains end to end, incl. the rake-link relation conv
    assert any("risk_head" in n for n in names)
    assert any("delay_head" in n for n in names)
    assert any("service__rake_link__service" in n for n in names)


def test_diffusion_conv_shape():
    x = torch.randn(5, 8)
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 4]])
    out = DiffusionConv(8, k_hops=2)(x, edge_index)
    assert out.shape == (5, 8)


def test_dcrnn_arch_runs():
    dm = CascadeDataModule(n_samples=4, seed=7)
    sample = dm.demo_sample("BSB")
    model = SpatioTemporalGNN({"model": {"hidden_dim": 16, "layers": 2, "arch": "dcrnn"}})
    out = model(sample)
    assert out["delay"].shape == (4,)
