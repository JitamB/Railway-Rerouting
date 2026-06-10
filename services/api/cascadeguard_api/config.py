"""Service configuration loaded from environment (see .env.example)."""

from __future__ import annotations

from pydantic import BaseModel


class Settings(BaseModel):
    redis_url: str = "redis://localhost:6379/0"
    stream_key: str = "cascadeguard.events"
    database_url: str = "postgresql://cascadeguard:cascadeguard@localhost:5432/cascadeguard"
    host: str = "0.0.0.0"
    port: int = 8000


def load_settings() -> Settings:
    """Build Settings from environment variables."""
    ...
