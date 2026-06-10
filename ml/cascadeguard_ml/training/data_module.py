"""Datamodule: assembles training windows from twin events + the dependency graph.

Pairs event-time delay sequences with the heterogeneous subgraph. Mixes real (calibrated)
running with **simulator-injected rare events** so the model sees the shape of derailment/fog
cascades it can't learn from normal logs (audit-04 §2/§6).
"""

from __future__ import annotations


class CascadeDataModule:
    def __init__(self, graph_artifact: str, events_source: str, window_min: int = 120) -> None:
        ...

    def train_dataloader(self) -> "object":
        ...

    def val_dataloader(self) -> "object":
        ...
