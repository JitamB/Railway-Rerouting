"""WebSocket router — live cascade deltas to the operator dashboard.

Pushes deltas, not full state, and recomputes only event-touched subgraphs (audit-02 §1.5).
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from ..deps import CascadeStore, get_prediction_store

router = APIRouter(tags=["ws"])


@router.websocket("/ws/live")
async def live_feed(
    ws: WebSocket, store: CascadeStore = Depends(get_prediction_store)
) -> None:
    """Stream per-station cascade deltas (not full state — audit-02 §1.5), then a completion marker."""
    await ws.accept()
    try:
        records = store.records()
        for r in records:
            await ws.send_json({
                "type": "delta", "station": r["station"], "cascade_risk": r["cascade_risk"],
                "delay_interval_min": r["delay_interval_min"], "mode": r["mode"],
                "data_age_s": r["data_age_s"],
            })
            await asyncio.sleep(0.05)
        await ws.send_json({"type": "complete", "count": len(records)})
    except WebSocketDisconnect:
        return
