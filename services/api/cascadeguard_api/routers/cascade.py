"""Cascade router — at-risk downstream stations for a given train."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/cascade", tags=["cascade"])


@router.get("/{train_no}")
def cascade_for_train(train_no: str) -> dict:
    """Return downstream stations at risk + probability for ``train_no``."""
    ...
