"""Primary adapter — reads events from the digital twin (data/simulator).

Deterministic and always-available; this is the spine on stage and in dev.
"""

from __future__ import annotations

from typing import Iterator


class TwinAdapter:
    """Streams ``TrainEvent``-shaped dicts from a running simulation."""

    def __init__(self, section_config: str) -> None:
        ...

    def stream(self) -> Iterator[dict]:
        """Yield normalized events conforming to shared/schemas/events.schema.json."""
        ...
