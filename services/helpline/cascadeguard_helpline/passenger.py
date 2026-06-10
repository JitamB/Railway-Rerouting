"""Fetch passenger details for a helpline case.

Resolves a PNR / passenger profile into the fields an authority needs (name, train, coach,
journey, contact). Reuses the ticketing mock from the reroute-engine and a profile store.
PII: fetch the minimum needed and attach only to the dispatched case.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PassengerDetails:
    passenger_id: str
    name: str
    pnr: str
    train_no: str
    coach: str | None
    journey: str          # e.g. "PNBE -> HWH"
    contact: str | None


def fetch_details(passenger_id: str, pnr: str | None = None) -> PassengerDetails:
    """Look up passenger/journey details (IRCTC mocked honestly where access is missing)."""
    ...
