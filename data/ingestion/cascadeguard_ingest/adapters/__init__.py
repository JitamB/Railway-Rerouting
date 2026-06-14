"""Source adapters + a factory keyed on CG_DATA_SOURCE.

Flipping the source swaps the adapter without touching anything downstream — every adapter
exposes the same ``stream() -> Iterator[dict]`` of schema-conformant events.
"""

from __future__ import annotations

from .coa_rtis_adapter import CoaRtisAdapter
from .ntes_scrape import NtesScrapeAdapter
from .twin_adapter import TwinAdapter
from .weather_tsr import WeatherTsrAdapter

__all__ = ["TwinAdapter", "CoaRtisAdapter", "NtesScrapeAdapter", "WeatherTsrAdapter", "get_adapter"]


def get_adapter(source: str, section_config: str | None = None, **kw):
    """Return the event-source adapter for CG_DATA_SOURCE in {twin, coa_rtis, ntes}."""
    if source == "twin":
        return TwinAdapter(section_config, **kw)
    if source == "coa_rtis":
        return CoaRtisAdapter(section_config=section_config, **kw)
    if source == "ntes":
        return NtesScrapeAdapter(**kw)
    raise ValueError(f"unknown CG_DATA_SOURCE {source!r} (expected twin|coa_rtis|ntes)")
