"""Per-cascade attribution — the "why" behind every alert (audit-03 §5).

GNNExplainer / attention attribution turns a prediction into a sentence: "this cascade is 60%
driven by the rake-link between 12301<->12302 and 30% by a platform conflict at PNBE." Pairs
with every passenger alert to convert a scary push into a trustworthy one.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Attribution:
    edge_type: str
    detail: str
    weight: float  # 0..1 contribution


class CascadeExplainer:
    def __init__(self, model: "object") -> None:
        ...

    def explain(self, subgraph: "object", node: str) -> list[Attribution]:
        """Return ranked edge-type contributions for a node's cascade risk."""
        ...

    def one_liner(self, attributions: list[Attribution]) -> str:
        """Render the top contributions as a single human-readable sentence."""
        ...
