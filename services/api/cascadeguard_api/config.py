"""Service configuration loaded from environment (see .env.example)."""

from __future__ import annotations

import os

from pydantic import BaseModel


class Settings(BaseModel):
    redis_url: str = "redis://localhost:6379/0"
    stream_key: str = "cascadeguard.events"
    database_url: str = "postgresql://cascadeguard:cascadeguard@localhost:5432/cascadeguard"
    host: str = "0.0.0.0"
    port: int = 8000
    disruption_station: str = "MGS"  # the twin disruption the demo serves predictions for


def load_settings() -> Settings:
    """Build Settings from environment variables, falling back to the defaults above."""
    d = Settings()
    return Settings(
        redis_url=os.getenv("REDIS_URL", d.redis_url),
        stream_key=os.getenv("STREAM_KEY", d.stream_key),
        database_url=os.getenv("DATABASE_URL", d.database_url),
        host=os.getenv("API_HOST", d.host),
        port=int(os.getenv("API_PORT", d.port)),
        disruption_station=os.getenv("DISRUPTION_STATION", d.disruption_station),
    )
