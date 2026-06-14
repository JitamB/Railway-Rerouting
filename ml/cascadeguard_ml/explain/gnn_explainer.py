"""Per-cascade attribution — the "why" behind every alert (audit-03 §5).

Occlusion-based GNNExplainer: for the target train, we remove each relation's edges feeding it
and measure how much the predicted delay moves. The relation with the biggest drop is the
dominant cause, and we name the specific upstream train on that edge. Turns a prediction into
"this cascade is 70% driven by the rake-link from 12301." Pairs with every passenger alert.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass
class Attribution:
    edge_type: str
    detail: str
    weight: float  # 0..1 contribution


class CascadeExplainer:
    def __init__(self, model: "object") -> None:
        self.model = model

    @torch.no_grad()
    def explain(self, data, node: str, service_names: list[str]) -> list[Attribution]:
        """Return ranked edge-type contributions for a service node's cascade risk."""
        self.model.eval()
        idx = service_names.index(node)
        base = float(self.model(data)["delay"][idx])

        deltas: dict[tuple, tuple[float, str]] = {}
        for rel, edge_index in data.edge_index_dict.items():
            # explain cascade drivers only: service->service delay-carrying edges. ``serves``
            # is static capacity context (no delay), not a cause, so it never attributes here.
            if rel[0] != "service" or rel[2] != "service" or edge_index.numel() == 0:
                continue
            incoming = (edge_index[1] == idx)
            if not bool(incoming.any()):
                continue
            masked = data.clone()
            masked[rel].edge_index = edge_index[:, ~incoming]
            delta = abs(base - float(self.model(masked)["delay"][idx]))
            src = service_names[int(edge_index[0][incoming][0])] if rel[0] == "service" else rel[0]
            deltas[rel] = (delta, src)

        total = sum(d for d, _ in deltas.values()) or 1.0
        attrs = [
            Attribution(rel[1], self._detail(rel, node, src), delta / total)
            for rel, (delta, src) in deltas.items()
        ]
        return sorted(attrs, key=lambda a: a.weight, reverse=True)

    def one_liner(self, attributions: list[Attribution]) -> str:
        """Render the top contributions as a single human-readable sentence."""
        top = [a for a in attributions if a.weight > 0.01][:2]
        if not top:
            return "no dominant cascade driver"
        return "; ".join(f"{a.weight:.0%} {a.edge_type.replace('_', '-')} ({a.detail})" for a in top)

    @staticmethod
    def _detail(rel: tuple, node: str, src: str) -> str:
        if rel[0] == "service":
            return f"{src}->{node}"
        return f"via {src}"
