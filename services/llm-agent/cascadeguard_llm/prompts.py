"""Structured prompt construction for the re-routing guidance.

Inputs: passenger origin/destination, current train status, top-k deterministic alternatives,
and time-sensitivity context. Output target: 2-3 sentences of plain-language guidance — with
the safety-critical fields supplied separately (templated), not asked of the model.
"""

from __future__ import annotations


def build_guidance_prompt(
    origin: str,
    dest: str,
    current_delay_min: float,
    risk: float,
    alternatives: list["object"],
    language: str = "en",
) -> str:
    """Return a structured prompt for plain-language re-route guidance."""
    ...
