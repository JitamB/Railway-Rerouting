"""Corridor router — the open Corridor Risk API (aggregate zone health).

Designed for third-party consumption (travel aggregators, corporate travel, state transport).
Rate-limited and documented via the auto-generated OpenAPI spec at /docs.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import CascadeStore, get_prediction_store

router = APIRouter(prefix="/corridor", tags=["corridor"])


@router.get("/{zone}")
def corridor_health(
    zone: str, store: CascadeStore = Depends(get_prediction_store)
) -> dict:
    """Return an aggregate corridor health score for ``zone`` (open Corridor Risk API)."""
    return store.corridor(zone)
