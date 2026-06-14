import numpy as np
import torch

from cascadeguard_ml.explain.gnn_explainer import CascadeExplainer
from cascadeguard_ml.ood.detector import OODDetector
from cascadeguard_ml.training.data_module import CascadeDataModule
from cascadeguard_ml.uncertainty.conformal import ConformalCalibrator


def _residuals_and_embeddings(model, dm):
    res, emb = [], []
    for batch in dm.val_dataloader():
        out = model(batch)
        res.append((out["delay"] - batch["service"].y_delay).detach())
        emb.append(out["embedding"].detach())
    return torch.cat(res).numpy(), torch.cat(emb).numpy()


def test_conformal_interval_achieves_coverage(trained_model):
    dm = CascadeDataModule(n_samples=200, seed=11)
    cal_res, _ = _residuals_and_embeddings(trained_model, dm)

    cal = ConformalCalibrator(target_coverage=0.90)
    cal.fit(cal_res)

    # check coverage on the held-out test split
    preds, targets = [], []
    for batch in dm.test_dataloader():
        preds.append(trained_model(batch)["delay"].detach())
        targets.append(batch["service"].y_delay)
    preds = torch.cat(preds).numpy()
    targets = torch.cat(targets).numpy()

    lo0, hi0 = cal.interval(0.0)
    assert lo0 == 0.0 and hi0 > 0.0                  # delay floored at 0
    lo, hi = cal.interval(20.0)
    assert lo < 20.0 < hi                            # interval brackets the point estimate
    assert cal.coverage(preds, targets) >= 0.80      # ~90% target, allow finite-sample slack


def test_ood_flags_far_embeddings(trained_model):
    dm = CascadeDataModule(n_samples=120, seed=12)
    _, emb = _residuals_and_embeddings(trained_model, dm)

    det = OODDetector(quantile=0.975)
    det.fit(emb)

    assert det.is_ood(emb.mean(axis=0)) is False        # an average in-dist point
    assert det.is_ood(emb.mean(axis=0) + 100.0) is True  # a wildly off-distribution embedding


def test_explainer_attributes_outbound_delay_to_rake_link(trained_model):
    dm = CascadeDataModule(n_samples=4, seed=13)
    sample = dm.demo_sample("MGS", start=30, duration=30)
    names = [n.split(":", 1)[1] for n in sorted(dm.sv_idx, key=lambda k: dm.sv_idx[k])]

    explainer = CascadeExplainer(trained_model)
    attrs = explainer.explain(sample, "12302", names)
    one_liner = explainer.one_liner(attrs)

    assert attrs, "expected at least one attribution"
    # 12302's delay is reachable only through the rake-link -> it must dominate
    assert attrs[0].edge_type == "rake_link"
    assert "rake-link" in one_liner
    print("\nwhy(12302):", one_liner)
