"""Intent classification + entity extraction for a helpline query.

Turns free text (already transcribed/translated) into a structured query: the grievance
category that drives authority routing, plus extracted entities (PNR, train, station, coach).
The LLM assists understanding; the resulting fields are validated before they drive dispatch.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Keyword lexicon per grievance category. Matches English *and* common romanized-Hindi terms, so
# routing works on a regional-language utterance without a real NMT engine (asr.translate is a
# passthrough mock). Categories mirror config/authorities.example.yaml.
_LEXICON: dict[str, list[str]] = {
    "security": ["bag", "lawaris", "unattended", "suspicious", "theft", "chori", "snatch",
                 "weapon", "rpf", "harass", "chhed", "fight", "jhagda", "security"],
    "medical": ["medical", "doctor", "sick", "bimar", "beemar", "injury", "chot", "heart",
                "faint", "behosh", "ambulance", "blood", "pain"],
    "cleanliness": ["dirty", "gandagi", "ganda", "toilet", "washroom", "unclean", "safai",
                    "saaf", "stink", "badboo", "smell", "garbage"],
    "catering": ["food", "khana", "meal", "catering", "water", "paani", "overcharge",
                 "expired", "stale", "pantry"],
    "electrical_ac": ["ac", "fan", "light", "charging", "socket", "power", "bijli", "cooling",
                      "not working", "switch"],
    "punctuality_delay": ["late", "delay", "deri", "der", "running", "kitni", "time", "kab"],
    "refund_ticketing": ["refund", "tdr", "cancel", "wapas", "fare", "charge", "booking"],
    "coach_maintenance": ["berth", "window", "broken", "toota", "kharab", "maintenance",
                          "leak", "seat"],
}

_INFO_CATEGORIES = {"punctuality_delay"}  # usually a lookup, not a complaint to dispatch

_CATEGORY_LABEL = {
    "security": "Security concern",
    "medical": "Medical assistance",
    "cleanliness": "Cleanliness issue",
    "catering": "Catering complaint",
    "electrical_ac": "Electrical/AC issue",
    "punctuality_delay": "Delay enquiry",
    "refund_ticketing": "Refund/ticketing",
    "coach_maintenance": "Coach maintenance",
    "general": "General query",
}


@dataclass
class Understanding:
    category: str                          # e.g. "security" | "medical" | "punctuality_delay"
    is_grievance: bool                     # vs a pure info query (delay/reroute lookup)
    entities: dict = field(default_factory=dict)  # {pnr, train_no, station, coach, ...}
    summary: str = ""                      # short human-readable summary for the case
    confidence: float = 0.0


def _extract_entities(text: str) -> dict:
    entities: dict = {}
    pnr = re.search(r"\b\d{10}\b", text)
    if pnr:
        entities["pnr"] = pnr.group()
    masked = text.replace(entities["pnr"], "") if "pnr" in entities else text
    train = re.search(r"\b\d{4,5}\b", masked)
    if train:
        entities["train_no"] = train.group()
    coach = re.search(r"\b([A-HSM][0-9]{1,2}|[A-Z]{1,2}[0-9]{1,2})\b", text)
    if coach:
        entities["coach"] = coach.group()
    return entities


class IntentEngine:
    """Rule-based classifier (offline, deterministic). An LLM refinement step could be layered on
    via ``model``, but the resulting category/entities are always validated before they drive
    dispatch — a misroute is worse than a clumsy summary."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model

    def understand(self, text: str, context: dict | None = None) -> Understanding:
        """Classify the query and extract entities; flags low confidence for fallback."""
        lowered = text.lower()
        scores = {
            cat: sum(1 for kw in kws if kw in lowered)
            for cat, kws in _LEXICON.items()
        }
        best = max(scores, key=lambda c: scores[c])
        hits = scores[best]

        if hits == 0:
            category, confidence = "general", 0.0
        else:
            category = best
            confidence = min(0.55 + 0.15 * hits, 0.95)

        entities = _extract_entities(text)
        label = _CATEGORY_LABEL.get(category, "General query")
        return Understanding(
            category=category,
            is_grievance=category not in _INFO_CATEGORIES and category != "general",
            entities=entities,
            summary=f"{label}: {text.strip()}"[:240],
            confidence=confidence,
        )
