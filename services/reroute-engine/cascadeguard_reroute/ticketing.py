"""Ticketing reality (audit-01 §5).

A reserved ticket is **not** valid on another train; the alternative may be WL/Tatkal/full.
IRCTC is not openly API'd, so availability is **mocked honestly** here — but it is *modelled*,
not ignored. A mistaken "just board it" is the fastest way to lose a domain juror.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Availability:
    train_no: str
    status: str   # "AVL" | "WL" | "TATKAL" | "FULL"
    seats: int


def is_ticket_valid_on(original_train: str, alternative_train: str) -> bool:
    """Reserved tickets are train-specific; returns True only for genuinely valid cases."""
    ...


def live_availability(train_no: str) -> Availability:
    """Mocked IRCTC availability lookup (clearly labelled as mocked in responses)."""
    ...
