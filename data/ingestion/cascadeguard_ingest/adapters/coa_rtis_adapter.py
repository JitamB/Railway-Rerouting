"""Production-path adapter (MOCKED) — the real RTIS->COA integration point.

RTIS (ISRO/IRNSS GPS, ~30s updates) -> COA (Control Office Application) is the operational
feed; it is **internal to Indian Railways and not open to developers** (audit-01 §3). This
adapter defines the clean interface we would plug into in production and returns mocked data
until that access exists.
"""

from __future__ import annotations

from typing import Iterator


class CoaRtisAdapter:
    """Interface to the (mocked) RTIS->COA feed."""

    def __init__(self, endpoint: str | None = None, mock: bool = True) -> None:
        ...

    def stream(self) -> Iterator[dict]:
        """Yield normalized events; mocked replay until real COA access exists."""
        ...
