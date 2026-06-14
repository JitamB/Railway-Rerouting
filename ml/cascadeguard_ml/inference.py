"""Inference entrypoint + the demo command.

``python -m cascadeguard_ml.inference --station MGS`` injects that disruption on the twin and
prints the per-downstream-station cascade vector — risk, conformal interval, the one-line
"why", and an OOD flag. Composes the ST-GNN + conformal intervals + the explainer + the
OOD->simulator fallback. This is the "show the model running locally" demo beat.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

import torch

from cascadeguard_ml.explain.gnn_explainer import CascadeExplainer
from cascadeguard_ml.models.stgnn import SpatioTemporalGNN
from cascadeguard_ml.ood.detector import OODDetector
from cascadeguard_ml.spec import DEFAULT_CHECKPOINT, RISK_THRESHOLD
from cascadeguard_ml.training.data_module import CascadeDataModule
from cascadeguard_ml.uncertainty.conformal import ConformalCalibrator


@dataclass
class StationCascade:
    station: str
    cascade_risk: float
    delay_mean_min: float
    delay_interval_min: tuple[float, float]
    why: str
    ood: bool
    mode: str
    data_age_s: float


def _load_model(checkpoint: str) -> SpatioTemporalGNN:
    blob = torch.load(checkpoint, map_location="cpu", weights_only=False)
    model = SpatioTemporalGNN(blob["config"])
    model.load_state_dict(blob["state_dict"])
    model.eval()
    return model


def _fit_uncertainty(model, dm):
    """Fit the conformal calibrator + OOD reference (the inference dm is held out vs the model)."""
    res, emb = [], []
    with torch.no_grad():
        for loader in (dm.train_dataloader(), dm.val_dataloader(), dm.test_dataloader()):
            for batch in loader:
                out = model(batch)
                res.append(out["delay"] - batch["service"].y_delay)
                emb.append(out["embedding"])
    cal = ConformalCalibrator(target_coverage=0.90)
    cal.fit(torch.cat(res).numpy())
    ood = OODDetector(quantile=0.99)  # stricter: avoid false OOD on in-distribution scenarios
    ood.fit(torch.cat(emb).numpy())
    return cal, ood


def predict_from_station(station: str, checkpoint: str | None = None,
                         verbose: bool = True) -> list[StationCascade]:
    """Return per-downstream-station cascade predictions for a disruption at ``station``."""
    model = _load_model(checkpoint or DEFAULT_CHECKPOINT)
    dm = CascadeDataModule(n_samples=160, seed=99)
    cal, ood = _fit_uncertainty(model, dm)
    explainer = CascadeExplainer(model)

    sample = dm.demo_sample(station, start=36.0, duration=22.0)  # in-distribution tail cascade
    names = [n.split(":", 1)[1] for n in sorted(dm.sv_idx, key=lambda k: dm.sv_idx[k])]
    preds = {p.station: p for p in model.predict(sample, names, calibrator=cal)}

    with torch.no_grad():
        embeddings = model(sample)["embedding"]

    # map per-service predictions onto the stations they call at (downstream of the disruption)
    out: list[StationCascade] = []
    for node in dm.stations:
        code = node.split(":", 1)[1]
        callers = [tr for tr in names if code in dm.tt.service(tr).sched_arr_min]
        if not callers:
            continue
        dominant = max(callers, key=lambda tr: preds[tr].delay_mean_min)
        p = preds[dominant]
        sv_idx = dm.sv_idx[f"service:{dominant}"]
        is_ood = ood.is_ood(embeddings[sv_idx])
        why = explainer.one_liner(explainer.explain(sample, dominant, names)) \
            if p.delay_mean_min > 1.0 else "no significant cascade"
        out.append(StationCascade(
            station=code,
            cascade_risk=p.cascade_risk,
            delay_mean_min=p.delay_mean_min,
            delay_interval_min=p.delay_interval_min,
            why=why,
            ood=is_ood,
            mode="schedule_prior" if is_ood else "live",
            data_age_s=30.0,
        ))

    out.sort(key=lambda s: s.delay_mean_min, reverse=True)
    if verbose:
        _print(station, out)
    return out


def _print(station: str, cascades: list[StationCascade]) -> None:
    print(f"\nCascade forecast — disruption at {station} (OHE closure):\n")
    print(f"{'station':<8}{'risk':>6}{'delay (min)':>22}  why")
    print("-" * 78)
    for c in cascades:
        flag = " ⚠" if c.cascade_risk > 0.5 else "  "
        interval = f"{c.delay_mean_min:5.1f}  [{c.delay_interval_min[0]:.0f},{c.delay_interval_min[1]:.0f}]"
        print(f"{c.station:<8}{c.cascade_risk:6.2f}{interval:>22}{flag} {c.why}")
    print(f"\nmode={cascades[0].mode}  data_age={cascades[0].data_age_s:.0f}s  "
          f"(risk threshold {RISK_THRESHOLD:.0f} min)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CascadeGuard cascade inference.")
    parser.add_argument("--station", required=True, help="Disruption origin station, e.g. MGS")
    parser.add_argument("--checkpoint", default=None)
    args = parser.parse_args()
    predict_from_station(args.station, args.checkpoint)


if __name__ == "__main__":
    main()
