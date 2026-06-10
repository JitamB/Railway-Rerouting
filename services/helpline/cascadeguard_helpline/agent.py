"""Helpline agent orchestrator.

Runs a grievance/query end-to-end:
  transcribe (if speech) -> understand -> fetch passenger details -> open case ->
  route to authority -> dispatch -> reply (text + optional speech).

Structured fields drive routing/dispatch; the LLM only phrases the human-readable parts.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HelplineReply:
    case_id: str
    text: str
    audio_url: str | None       # set if a spoken reply was synthesized
    authority: str              # department the case was routed to
    status: str                 # initial case status, e.g. "open"


class HelplineAgent:
    def __init__(self, language: str = "en") -> None:
        ...

    def handle(
        self,
        passenger_id: str,
        text: str | None = None,
        audio: bytes | None = None,
        language: str | None = None,
    ) -> HelplineReply:
        """Process one helpline turn (text or speech) and return a reply + opened case."""
        ...


def run() -> None:
    """Service entrypoint (consumes helpline requests; wired behind services/api)."""
    ...


if __name__ == "__main__":
    run()
