from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ClaimCondition(str, Enum):
    clear = "Clear"
    heavy_rain = "Heavy Rain"
    blizzard = "Blizzard"


class ClaimStatus(str, Enum):
    approved = "APPROVED"
    denied = "DENIED"
    review = "REVIEW"


class DriverProfile(BaseModel):
    driver_id: str
    display_name: str
    home_base: str


class ClaimSubmission(BaseModel):
    driver_id: str = Field(min_length=3)
    location_query: str = Field(min_length=3, description="Human-readable address/city")
    claim_start_utc: datetime
    claim_end_utc: datetime
    claimed_condition: ClaimCondition


class OracleSnapshot(BaseModel):
    latitude: float
    longitude: float
    precipitation_mm: float
    wind_speed_kmh: float
    snowfall_cm: float
    observed_condition: ClaimCondition


class ClaimDecision(BaseModel):
    claim_id: str
    driver_id: str
    status: ClaimStatus
    approved_hours: float
    payout_usd: float
    reason: str
    strikes_after_decision: int
    restricted: bool
    oracle: OracleSnapshot
    processed_at: datetime


class DriverForensicState(BaseModel):
    driver_id: str
    display_name: str
    strikes: int
    approved_claims: int
    denied_claims: int
    restricted: bool
    forensic_history_score: float


class DashboardSnapshot(BaseModel):
    generated_at: datetime
    total_claims: int
    approval_rate: float
    local_volatility: float
    traffic_density: float
    forensic_history_risk: float
    real_time_risk_score: float
    risk_trend: list[float]
    payout_exposure_usd: float


class PolicyRule(BaseModel):
    title: str
    detail: str


class PolicyDocument(BaseModel):
    generated_at: datetime
    payout_rules: dict[str, float]
    strike_policy: list[PolicyRule]
    consensus_description: list[PolicyRule]
