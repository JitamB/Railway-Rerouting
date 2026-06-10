"""Inference entrypoint + the demo command.

``python -m cascadeguard_ml.inference --station PNBE`` prints the per-station cascade
probability vector — the "show the model running locally" demo beat (intuition §9). Combines
the ST-GNN, conformal intervals, the explainer's one-liner, and the OOD->simulator fallback.
"""

from __future__ import annotations

import argparse


def predict_from_station(station: str, checkpoint: str | None = None) -> list:
    """Return per-downstream-station NodePrediction objects for a disruption at ``station``."""
    ...


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CascadeGuard cascade inference.")
    parser.add_argument("--station", required=True, help="Origin station code, e.g. PNBE")
    parser.add_argument("--checkpoint", default=None)
    args = parser.parse_args()
    predict_from_station(args.station, args.checkpoint)


if __name__ == "__main__":
    main()
