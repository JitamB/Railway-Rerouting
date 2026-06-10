"""Queries router — a passenger's past helpline queries and their status.

Backs the 'My Queries' screen: list cases (newest first) with status
(open / in_progress / resolved / rejected) and drill into one case's history. Each passenger
sees only their own cases.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/queries", tags=["queries"])


@router.get("")
def list_queries(passenger_id: str) -> dict:
    """Return the passenger's past queries with current status, newest first."""
    ...


@router.get("/{case_id}")
def query_detail(case_id: str, passenger_id: str) -> dict:
    """Return one case with its message/status history."""
    ...
