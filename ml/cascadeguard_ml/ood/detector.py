"""Out-of-distribution detection -> simulator fallback (audit-04 §2).

Black-swan disruptions (derailment, OHE failure, blockade) have no historical analog; a
data-driven model will confidently mis-predict exactly when stakes are highest. We fit the
in-distribution reference as a Gaussian over training embeddings; an event whose Mahalanobis
distance exceeds the calibrated threshold is flagged OOD, and the system falls back to the
discrete-event simulator and widens its intervals.
"""

from __future__ import annotations

import numpy as np


def _as_2d(x) -> np.ndarray:
    arr = x.detach().cpu().numpy() if hasattr(x, "detach") else np.asarray(x, dtype=float)
    return arr.reshape(1, -1) if arr.ndim == 1 else arr


class OODDetector:
    def __init__(self, method: str = "mahalanobis", threshold: float = 0.0,
                 quantile: float = 0.975) -> None:
        self.method = method
        self.threshold = threshold
        self.quantile = quantile
        self.mean: np.ndarray | None = None
        self.inv_cov: np.ndarray | None = None

    def fit(self, embeddings) -> None:
        """Fit the in-distribution reference (mean + covariance) from training embeddings."""
        x = _as_2d(embeddings)
        self.mean = x.mean(axis=0)
        cov = np.cov(x, rowvar=False) + 1e-3 * np.eye(x.shape[1])
        self.inv_cov = np.linalg.inv(cov)
        # calibrate the threshold to a quantile of in-distribution distances
        self.threshold = float(np.quantile(self._distance(x), self.quantile))

    def _distance(self, x: np.ndarray) -> np.ndarray:
        diff = x - self.mean
        return np.sqrt(np.einsum("ij,jk,ik->i", diff, self.inv_cov, diff))

    def is_ood(self, embedding) -> bool:
        """True if the event is off-distribution and should trigger simulator fallback."""
        if self.mean is None:
            raise RuntimeError("call fit() before is_ood()")
        return bool(self._distance(_as_2d(embedding))[0] > self.threshold)
