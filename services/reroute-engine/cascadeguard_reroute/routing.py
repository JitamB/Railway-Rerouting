"""Deterministic alternative-train query.

Given an origin/destination and current time, return the top-k candidate alternatives. This is
the deterministic part the LLM later phrases — the model predicts, the router enumerates, the
allocator chooses (clear separation of concerns).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Candidate:
    train_no: str
    platform: str
    departs_min: float
    arrives_dest_min: float


def find_alternatives(origin: str, dest: str, after_min: float, k: int = 3) -> list[Candidate]:
    """Return up to ``k`` candidate trains from ``origin`` to ``dest`` after ``after_min``."""
    ...
