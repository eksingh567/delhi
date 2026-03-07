from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class RiskLevel(str, Enum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"


@dataclass
class GeopoliticalSignals:
    country: str
    news_severity: float
    military_activity: float
    diplomatic_tension: float
    economic_sanctions: float
    social_sentiment: float
    historical_pattern: float


@dataclass
class RiskAssessment:
    country: str
    probability_of_escalation: float
    risk_level: RiskLevel
    expected_timeframe_weeks: str
    generated_at: datetime


@dataclass
class StudentRegistration:
    student_id: str
    full_name: str
    email: str
    phone: str
    university: str
    country: str
    city: str
    passport_last4: str
    emergency_contact: str
    location_sharing_enabled: bool = False


@dataclass
class StudentStatus:
    student_id: str
    safety_status: str
    latest_update: datetime


@dataclass
class Alert:
    country: str
    risk_level: RiskLevel
    message: str
    recommended_exit_routes: List[str]
    generated_at: datetime


@dataclass
class EvacuationRequest:
    country: str
    origin_city: str
    target_safe_hub: str
    student_count: int
    avoid_nodes: Optional[List[str]] = field(default=None)


@dataclass
class EvacuationPlan:
    route: List[str]
    estimated_travel_time_hours: float
    risk_score: str
    transport_capacity: int
    embassy_contact_point: str
