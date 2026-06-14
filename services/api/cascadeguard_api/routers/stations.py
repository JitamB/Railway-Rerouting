"""Stations router — incoming trains with delay probability and ETA range."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import CascadeStore, get_prediction_store

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("/{code}")
def station_view(
    code: str, store: CascadeStore = Depends(get_prediction_store)
) -> dict:
    """Return incoming trains at station ``code`` with delay probability + ETA window."""
    return store.for_station(code)
