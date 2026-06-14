"""Structured prompt construction for the re-routing guidance.

Inputs: passenger origin/destination, current train status, top-k deterministic alternatives,
and time-sensitivity context. Output target: 2-3 sentences of plain-language guidance — with
the safety-critical fields supplied here (templated), the model asked only to phrase them.
"""

from __future__ import annotations


def _fmt_alt(alt) -> str:
    # accepts a routing.Candidate (attrs) or a plain dict
    g = (lambda k: getattr(alt, k)) if hasattr(alt, "train_no") else alt.__getitem__
    return (f"- train {g('train_no')} from platform {g('platform')}, "
            f"departs +{g('departs_min'):.0f} min, reaches {g('arrives_dest_min'):.0f} min")


def build_guidance_prompt(
    origin: str,
    dest: str,
    current_delay_min: float,
    risk: float,
    alternatives: list["object"],
    language: str = "en",
) -> str:
    """Return a structured prompt for plain-language re-route guidance."""
    alts = "\n".join(_fmt_alt(a) for a in alternatives) or "- (none available)"
    lang_note = "" if language == "en" else f"\nRespond in language code '{language}' (keep all numbers/codes unchanged)."
    return (
        "Rephrase this re-route guidance for the passenger. Keep every number exactly.\n\n"
        f"Journey: {origin} -> {dest}\n"
        f"Current train delay: {current_delay_min:.0f} min\n"
        f"Cascade risk: {risk:.0%}\n"
        f"Feasible alternatives (already capacity-checked):\n{alts}\n"
        f"{lang_note}"
    )
