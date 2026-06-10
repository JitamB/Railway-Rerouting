"""Intent classification + entity extraction for a helpline query.

Turns free text (already transcribed/translated) into a structured query: the grievance
category that drives authority routing, plus extracted entities (PNR, train, station, coach).
The LLM assists understanding; the resulting fields are validated before they drive dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Understanding:
    category: str                          # e.g. "security" | "medical" | "punctuality_delay"
    is_grievance: bool                     # vs a pure info query (delay/reroute lookup)
    entities: dict = field(default_factory=dict)  # {pnr, train_no, station, coach, ...}
    summary: str = ""                      # short human-readable summary for the case
    confidence: float = 0.0


class IntentEngine:
    def __init__(self, model: str | None = None) -> None:
        ...

    def understand(self, text: str, context: dict | None = None) -> Understanding:
        """Classify the query and extract entities; flags low confidence for fallback."""
        ...
