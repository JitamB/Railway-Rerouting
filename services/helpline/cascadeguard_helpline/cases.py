"""Case lifecycle + history.

A helpline query becomes a tracked case the passenger can follow. Status lifecycle:
``open -> in_progress -> resolved`` (or ``rejected``). Persisted to the grievance tables
(infra/db/init.sql); each passenger sees only their own cases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


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
    status: CaseStatus = CaseStatus.OPEN
    created_at: str = ""
    updated_at: str = ""
    transcript: str = ""
    messages: list = field(default_factory=list)


def open_case(passenger_id: str, understanding: "object", details: "object", authority: "object") -> Case:
    """Create and persist a new case from the agent's understanding + routing decision."""
    ...


def list_cases(passenger_id: str) -> list[Case]:
    """Return a passenger's past queries, newest first (for the 'My Queries' view)."""
    ...


def update_status(case_id: str, status: CaseStatus, note: str | None = None) -> Case:
    """Advance a case's status (e.g. on an authority callback) and append a history note."""
    ...
