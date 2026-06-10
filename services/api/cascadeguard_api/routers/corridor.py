"""Corridor router — the open Corridor Risk API (aggregate zone health).

Designed for third-party consumption (travel aggregators, corporate travel, state transport).
Rate-limited and documented via the auto-generated OpenAPI spec at /docs.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/corridor", tags=["corridor"])


@router.get("/{zone}")
def corridor_health(zone: str) -> dict:
    """Return an aggregate corridor health score for ``zone``."""
    ...
