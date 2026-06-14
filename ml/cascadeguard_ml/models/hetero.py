"""Heterogeneous message passing over the multi-relational dependency graph.

Per-edge-type relational layers for {block, platform, rake-link, crew, loco, serves}, each with
a learnable gate (the "learned adjacency": the model decides how much each edge type matters —
the rake-link gate is the high-value one, audit-02 §3.2/§3.4). Messages flow cause→effect so a
node aggregates its upstream causes. The per-relation contributions are exposed for the
explainer's one-liner.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import SAGEConv

from .layers import DiffusionConv


def _key(rel: tuple) -> str:
    return "__".join(rel)


class HeteroLayer(nn.Module):
    def __init__(self, node_types: list[str], relations: list[tuple], hidden: int,
                 arch: str = "graph_wavenet") -> None:
        super().__init__()
        self.convs = nn.ModuleDict()
        self.gates = nn.ParameterDict()
        for rel in relations:
            src, _, dst = rel
            if src == dst:
                conv = DiffusionConv(hidden) if arch == "dcrnn" else SAGEConv(hidden, hidden)
            else:
                conv = SAGEConv((hidden, hidden), hidden)  # bipartite (e.g. service->station)
            self.convs[_key(rel)] = conv
            self.gates[_key(rel)] = nn.Parameter(torch.ones(1))
        self.self_lin = nn.ModuleDict({nt: nn.Linear(hidden, hidden) for nt in node_types})

    def forward(self, x_dict, edge_index_dict, return_contrib: bool = False):
        out = {nt: self.self_lin[nt](x) for nt, x in x_dict.items()}
        contrib = {nt: {} for nt in x_dict}
        for rel, edge_index in edge_index_dict.items():
            key = _key(rel)
            if key not in self.convs or edge_index.numel() == 0:
                continue
            src, _, dst = rel
            conv = self.convs[key]
            msg = conv(x_dict[src], edge_index) if src == dst \
                else conv((x_dict[src], x_dict[dst]), edge_index)
            gated = F.softplus(self.gates[key]) * msg
            out[dst] = out[dst] + gated
            if return_contrib:
                contrib[dst][rel] = gated.detach()
        out = {nt: F.relu(h) for nt, h in out.items()}
        return (out, contrib) if return_contrib else out

    def gate_value(self, rel: tuple) -> float:
        return float(F.softplus(self.gates[_key(rel)]))


class HeteroEncoder(nn.Module):
    """Per-edge-type relational encoder feeding the temporal stack in stgnn.py."""

    def __init__(self, node_types: list[str], relations: list[tuple], hidden_dim: int,
                 layers: int = 4, arch: str = "graph_wavenet") -> None:
        super().__init__()
        self.relations = relations
        self.blocks = nn.ModuleList(
            HeteroLayer(node_types, relations, hidden_dim, arch) for _ in range(layers)
        )

    def forward(self, x_dict, edge_index_dict, return_contrib: bool = False):
        """Return per-node embeddings aggregated across edge types (+ last-layer contributions)."""
        contrib = None
        for i, block in enumerate(self.blocks):
            if return_contrib and i == len(self.blocks) - 1:
                x_dict, contrib = block(x_dict, edge_index_dict, return_contrib=True)
            else:
                x_dict = block(x_dict, edge_index_dict)
        return (x_dict, contrib) if return_contrib else x_dict
