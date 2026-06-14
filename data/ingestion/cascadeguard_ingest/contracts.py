"""Load + validate against the frozen shared event contract.

``shared/schemas/events.schema.json`` lives outside the Python packages; with editable
installs the source stays in the tree, so we resolve it relative to the repo root. Every
adapter and the anomaly gate validate here so nothing off-contract reaches the graph/model.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator

_REPO_ROOT = Path(__file__).resolve().parents[3]
_EVENTS_SCHEMA_PATH = _REPO_ROOT / "shared" / "schemas" / "events.schema.json"


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(_EVENTS_SCHEMA_PATH.read_text()))


def event_errors(event: dict) -> list[str]:
    """Return human-readable schema violations for an event ([] means valid)."""
    return [e.message for e in _validator().iter_errors(event)]


def is_valid_event(event: dict) -> bool:
    return not event_errors(event)
