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
