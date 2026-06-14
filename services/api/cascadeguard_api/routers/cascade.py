"""Cascade router — at-risk downstream stations for a given train."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import CascadeStore, get_prediction_store

router = APIRouter(prefix="/cascade", tags=["cascade"])


@router.get("/{train_no}")
def cascade_for_train(
    train_no: str, store: CascadeStore = Depends(get_prediction_store)
) -> dict:
    """Return downstream stations at risk + probability for ``train_no`` (with staleness watermark)."""
    return store.for_train(train_no)
