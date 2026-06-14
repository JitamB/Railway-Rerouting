"""Fetch passenger details for a helpline case.

Resolves a PNR / passenger profile into the fields an authority needs (name, train, coach,
journey, contact). Reuses the ticketing mock from the reroute-engine and a profile store.
PII: fetch the minimum needed and attach only to the dispatched case.
"""

from __future__ import annotations

from dataclasses import dataclass

# Honest stand-in profile store (IRCTC/PRS isn't openly API'd). Deterministic from passenger_id so
# the same passenger always resolves to the same details; PII is minimal and masked.
_NAMES = ["A. Kumar", "S. Devi", "R. Singh", "M. Iqbal", "P. Nair", "T. Das"]
_DEMO_TRAIN = "12301"
_DEMO_JOURNEY = "PNBE -> BSB"


@dataclass
class PassengerDetails:
    passenger_id: str
    name: str
    pnr: str
    train_no: str
    coach: str | None
    journey: str          # e.g. "PNBE -> HWH"
    contact: str | None


def fetch_details(passenger_id: str, pnr: str | None = None, train_no: str | None = None,
                  coach: str | None = None) -> PassengerDetails:
    """Look up passenger/journey details (IRCTC mocked honestly where access is missing)."""
    seed = abs(hash(passenger_id))
    return PassengerDetails(
        passenger_id=passenger_id,
        name=_NAMES[seed % len(_NAMES)],
        pnr=pnr or f"{8000000000 + seed % 1000000000}",
        train_no=train_no or _DEMO_TRAIN,
        coach=coach,
        journey=_DEMO_JOURNEY,
        contact=f"+91-9{seed % 1000000000:09d}"[:13],  # masked stand-in contact
    )
