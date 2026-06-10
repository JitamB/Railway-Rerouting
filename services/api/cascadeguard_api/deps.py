"""Shared FastAPI dependencies (Redis handle, latest-prediction store access)."""

from __future__ import annotations


def get_redis():
    """Return a Redis connection for reading the live prediction stream."""
    ...


def get_prediction_store():
    """Return an accessor for the latest per-station cascade predictions."""
    ...
