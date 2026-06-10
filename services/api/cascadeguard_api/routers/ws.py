"""WebSocket router — live cascade deltas to the operator dashboard.

Pushes deltas, not full state, and recomputes only event-touched subgraphs (audit-02 §1.5).
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket

router = APIRouter(tags=["ws"])


@router.websocket("/ws/live")
async def live_feed(ws: WebSocket) -> None:
    """Stream cascade-risk deltas as new disruptions are processed."""
    ...
