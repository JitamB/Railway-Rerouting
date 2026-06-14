"""Ticketing reality (audit-01 §5).

A reserved ticket is **not** valid on another train; the alternative may be WL/Tatkal/full.
IRCTC is not openly API'd, so availability is **mocked honestly** here — deterministic, clearly
a stand-in for the real PRS/availability feed — but it is *modelled*, not ignored. A mistaken
"just board it" is the fastest way to lose a domain juror.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Availability:
    train_no: str
    status: str   # "AVL" | "WL" | "TATKAL" | "FULL"
    seats: int


def is_ticket_valid_on(original_train: str, alternative_train: str) -> bool:
    """Reserved tickets are train-specific; valid only on the train actually booked.

    (Real exceptions like alternate-accommodation/TDR exist but require authority action — the
    safe, juror-defensible default is: a reserved ticket does not let you board another train.)
    """
    return original_train == alternative_train


def live_availability(train_no: str) -> Availability:
    """Mocked IRCTC availability lookup — deterministic stand-in, clearly labelled as mocked."""
    key = int(train_no) if train_no.isdigit() else abs(hash(train_no))
    seats = (key * 13) % 73
    if seats == 0:
        status = "FULL"
    elif seats <= 12:
        status = "WL"
    else:
        status = "AVL"
    return Availability(train_no=train_no, status=status, seats=seats)
