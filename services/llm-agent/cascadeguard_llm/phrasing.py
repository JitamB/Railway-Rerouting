"""Template-first phrasing with optional async LLM enrichment (audit-02 §1.4/§3.5).

``render_template`` returns a usable alert immediately from a deterministic template.
``enrich`` may later replace the prose with LLM phrasing when Claude is reachable — but it
falls back to the template on any failure, and if ``safety_fields`` are given it rejects any
LLM output that dropped a safety-critical value (train no., platform, time), so those fields
are always the templated ones, never the model's.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "?"  # a missing field shows a visible gap rather than crashing the alert


@lru_cache(maxsize=8)
def _load_bands(language: str) -> dict[str, str]:
    path = TEMPLATES_DIR / f"{language}.delay-bands.txt"
    if not path.exists():
        path = TEMPLATES_DIR / "en.delay-bands.txt"  # fall back to English
    bands = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        band, text = line.split("|", 1)
        bands[band.strip()] = text.strip()
    return bands


def render_template(delay_band: str, language: str, fields: dict) -> str:
    """Instant, deterministic alert text for the offline/degraded path."""
    bands = _load_bands(language)
    template = bands.get(delay_band) or bands.get("low", "")
    return template.format_map(_SafeDict(fields))


async def enrich(template_text: str, prompt: str, client: "object",
                 safety_fields: list[str] | None = None) -> str:
    """Optionally upgrade prose via Claude; falls back to ``template_text`` on any failure."""
    try:
        prose = await client.phrase(prompt)
    except Exception:
        return template_text  # network/LLM unavailable — the templated alert already shipped
    if not prose:
        return template_text
    if safety_fields and not all(str(f) in prose for f in safety_fields):
        return template_text  # the model dropped a safety-critical field — keep the template
    return prose
