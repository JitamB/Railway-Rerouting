"""FastAPI application entrypoint.

Mounts the routers and exposes ``GET /health``. OpenAPI docs auto-generated at ``/docs``.
Business logic lives in the routers and the re-route/worker services — this module just wires
them together.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import cascade, corridor, helpline, queries, reroute, stations, ws

app = FastAPI(title="CascadeGuard API", version="0.0.0")

# The operator dashboard (Vite, :3001) and the Expo web preview call this cross-origin. Permissive
# for the single-zone demo; production restricts the allow-list to the deployed frontends.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness probe."""
    return {"status": "ok"}


app.include_router(cascade.router)
app.include_router(stations.router)
app.include_router(corridor.router)
app.include_router(reroute.router)
app.include_router(helpline.router)
app.include_router(queries.router)
app.include_router(ws.router)
