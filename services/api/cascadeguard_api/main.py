"""FastAPI application entrypoint.

Mounts the routers and exposes ``GET /health``. OpenAPI docs auto-generated at ``/docs``.
Business logic lives in the routers and the re-route/worker services — this module just wires
them together.
"""

from __future__ import annotations

from fastapi import FastAPI

from .routers import cascade, corridor, reroute, stations, ws

app = FastAPI(title="CascadeGuard API", version="0.0.0")


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness probe."""
    return {"status": "ok"}


app.include_router(cascade.router)
app.include_router(stations.router)
app.include_router(corridor.router)
app.include_router(reroute.router)
app.include_router(ws.router)
