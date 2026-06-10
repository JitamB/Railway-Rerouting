"""API response/request models. The cross-service event contract lives in shared/schemas/."""

from __future__ import annotations

from pydantic import BaseModel


class StationRisk(BaseModel):
    station: str
    cascade_risk: float
    delay_interval_min: tuple[float, float]
    why: str
    data_age_s: float  # staleness watermark (audit-04 §1)


class RerouteOption(BaseModel):
    train_no: str
    platform: str
    departs: str
    arrives_dest: str
    seats_status: str  # "AVL" | "WL" | "TATKAL" | "FULL"


class RerouteResponse(BaseModel):
    pnr: str
    current_risk: float
    options: list[RerouteOption]
    guidance: str


class HelplineReply(BaseModel):
    case_id: str
    text: str
    audio_url: str | None = None  # set when a spoken (TTS) reply is returned
    authority: str                # department the case was routed to
    status: str                   # case status, e.g. "open"


class QuerySummary(BaseModel):
    case_id: str
    category: str
    department: str
    summary: str
    status: str                   # open | in_progress | resolved | rejected
    created_at: str
    updated_at: str
