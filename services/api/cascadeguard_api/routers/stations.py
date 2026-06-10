"""Stations router — incoming trains with delay probability and ETA range."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("/{code}")
def station_view(code: str) -> dict:
    """Return incoming trains at station ``code`` with delay probability + ETA window."""
    ...
