"""Case lifecycle + history.

A helpline query becomes a tracked case the passenger can follow. Status lifecycle:
``open -> in_progress -> resolved`` (or ``rejected``). Persisted to the grievance tables
(infra/db/init.sql); each passenger sees only their own cases.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

# In-memory store (process-lifetime), shared by the agent and the API in the demo. The columns
# mirror infra/db/init.sql `grievance_cases` / `grievance_events`; the production path swaps this
# for those tables behind the same functions. PII-bearing: scope every read to the owner.
_CASES: dict[str, "Case"] = {}
_SEQ = itertools.count(1)


class CaseStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


@dataclass
class Case:
    case_id: str
    passenger_id: str
    category: str
    department: str
    summary: str
    language: str
    channel: str = "railmadad"
    external_reference: str = ""
    input_mode: str = "text"           # 'text' | 'speech'
    status: CaseStatus = CaseStatus.OPEN
    created_at: str = ""
    updated_at: str = ""
    transcript: str = ""
    messages: list = field(default_factory=list)  # history: [{at, status, note}]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def open_case(
    passenger_id: str,
    understanding: "object",
    details: "object",
    authority: "object",
    *,
    language: str = "en",
    transcript: str = "",
    input_mode: str = "text",
) -> Case:
    """Create and persist a new case from the agent's understanding + routing decision."""
    now = _now()
    case = Case(
        case_id=f"CG-{datetime.now(timezone.utc).year}-{next(_SEQ):06d}",
        passenger_id=passenger_id,
        category=understanding.category,
        department=authority.department,
        summary=understanding.summary,
        language=language,
        channel=authority.channel,
        input_mode=input_mode,
        status=CaseStatus.OPEN,
        created_at=now,
        updated_at=now,
        transcript=transcript,
        messages=[{"at": now, "status": "open", "note": "case created from helpline"}],
    )
    _CASES[case.case_id] = case
    return case


def get_case(case_id: str) -> Case | None:
    """Return one case (the 'My Queries' detail view)."""
    return _CASES.get(case_id)


def list_cases(passenger_id: str) -> list[Case]:
    """Return a passenger's past queries, newest first (for the 'My Queries' view)."""
    owned = [c for c in _CASES.values() if c.passenger_id == passenger_id]
    return sorted(owned, key=lambda c: c.created_at, reverse=True)


def update_status(case_id: str, status: CaseStatus, note: str | None = None) -> Case:
    """Advance a case's status (e.g. on an authority callback) and append a history note."""
    case = _CASES[case_id]
    case.status = status
    case.updated_at = _now()
    case.messages.append({"at": case.updated_at, "status": status.value, "note": note or ""})
    return case
