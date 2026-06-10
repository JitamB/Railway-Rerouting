"""Template-first phrasing with optional async LLM enrichment (audit-02 §1.4/§3.5).

``render`` returns a usable alert immediately from a deterministic template. ``enrich`` may
later replace the prose with LLM phrasing when Claude is reachable — but the safety-critical
fields (train no., platform, time) are always taken from the template, never the model.
"""

from __future__ import annotations


def render_template(delay_band: str, language: str, fields: dict) -> str:
    """Instant, deterministic alert text for the offline/degraded path."""
    ...


async def enrich(template_text: str, prompt: str, client: "object") -> str:
    """Optionally upgrade prose via Claude; falls back to ``template_text`` on any failure."""
    ...
