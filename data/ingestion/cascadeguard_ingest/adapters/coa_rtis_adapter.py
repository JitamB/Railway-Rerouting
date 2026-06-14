"""Production-path adapter (MOCKED) — the real RTIS->COA integration point.

RTIS (ISRO/IRNSS GPS, ~30s updates) -> COA (Control Office Application) is the operational
feed; it is **internal to Indian Railways and not open to developers** (audit-01 §3). This
adapter defines the clean interface we would plug into in production and returns mocked data
until that access exists — a replay of the digital twin, re-tagged ``source=coa_rtis`` with a
realistic ~30 s data-age, so downstream code is identical to the real feed's.
"""

from __future__ import annotations

from typing import Iterator

from .twin_adapter import TwinAdapter


class CoaRtisAdapter:
    """Interface to the (mocked) RTIS->COA feed."""

    def __init__(
        self, endpoint: str | None = None, mock: bool = True, section_config: str | None = None, **kw
    ) -> None:
        self.endpoint = endpoint
        self.mock = mock
        if mock:
            if section_config is None:
                raise ValueError("mock CoaRtisAdapter needs section_config to replay the twin")
            self._backing = TwinAdapter(section_config, source="coa_rtis", **kw)

    def stream(self) -> Iterator[dict]:
        """Yield normalized events; mocked replay until real COA access exists."""
        if not self.mock:
            raise NotImplementedError("real RTIS->COA access is internal to IR (audit-01 §3)")
        yield from self._backing.stream()
