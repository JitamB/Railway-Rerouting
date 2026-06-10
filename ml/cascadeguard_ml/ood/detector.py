"""Out-of-distribution detection -> simulator fallback (audit-04 §2).

Black-swan disruptions (derailment, OHE failure, blockade) have no historical analog; a
data-driven model will confidently mis-predict exactly when stakes are highest. When an event
scores OOD (Mahalanobis / energy on embeddings), the system switches to the discrete-event
simulator to project propagation from first principles and widens intervals.
"""

from __future__ import annotations


class OODDetector:
    def __init__(self, method: str = "mahalanobis", threshold: float = 0.0) -> None:
        ...

    def fit(self, embeddings: "object") -> None:
        """Fit the in-distribution reference from training embeddings."""
        ...

    def is_ood(self, embedding: "object") -> bool:
        """True if the event is off-distribution and should trigger simulator fallback."""
        ...
