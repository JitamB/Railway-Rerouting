"""Queries router — a passenger's past helpline queries and their status.

Backs the 'My Queries' screen: list cases (newest first) with status
(open / in_progress / resolved / rejected) and drill into one case's history. Each passenger
sees only their own cases.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from cascadeguard_helpline.cases import Case, get_case, list_cases

router = APIRouter(prefix="/queries", tags=["queries"])


def _summary(c: Case) -> dict:
    return {
        "case_id": c.case_id,
        "category": c.category,
        "department": c.department,
        "summary": c.summary,
        "status": c.status.value,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


@router.get("")
def list_queries(passenger_id: str) -> list[dict]:
    """Return the passenger's past queries with current status, newest first."""
    return [_summary(c) for c in list_cases(passenger_id)]


@router.get("/{case_id}")
def query_detail(case_id: str, passenger_id: str) -> dict:
    """Return one case with its message/status history (owner-scoped)."""
    case = get_case(case_id)
    if case is None or case.passenger_id != passenger_id:
        raise HTTPException(status_code=404, detail="case not found")
    return {**_summary(case), "transcript": case.transcript, "history": case.messages}
