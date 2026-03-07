from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import heapq
from typing import Dict, List, Tuple

from .models import (
    Alert,
    EvacuationPlan,
    EvacuationRequest,
    GeopoliticalSignals,
    RiskAssessment,
    RiskLevel,
    StudentRegistration,
)


@dataclass
class Edge:
    destination: str
    travel_time_hours: float
    risk_penalty: float


WEIGHTS = {
    "news_severity": 0.18,
    "military_activity": 0.27,
    "diplomatic_tension": 0.2,
    "economic_sanctions": 0.1,
    "social_sentiment": 0.1,
    "historical_pattern": 0.15,
}

COUNTRY_NETWORKS: Dict[str, Dict[str, List[Edge]]] = {
    "Ukraine": {
        "Kharkiv": [Edge("Kyiv", 7, 25), Edge("Dnipro", 4, 35)],
        "Dnipro": [Edge("Kyiv", 6, 30), Edge("Lviv", 9, 22)],
        "Kyiv": [Edge("Lviv", 7, 18)],
        "Lviv": [Edge("Poland Border", 3, 8)],
        "Poland Border": [],
    }
}

EMBASSY_CONTACTS = {
    "Ukraine": "+380-44-000-0000",
}


class SafePassEngine:
    def __init__(self) -> None:
        self._students: Dict[str, StudentRegistration] = {}

    @staticmethod
    def _risk_level(score: float) -> RiskLevel:
        if score >= 70:
            return RiskLevel.high
        if score >= 40:
            return RiskLevel.medium
        return RiskLevel.low

    @staticmethod
    def _timeframe(probability: float) -> str:
        if probability >= 80:
            return "1-3 weeks"
        if probability >= 60:
            return "3-6 weeks"
        return "6+ weeks"

    def assess_risk(self, signals: GeopoliticalSignals) -> RiskAssessment:
        weighted_sum = sum(getattr(signals, key) * weight for key, weight in WEIGHTS.items())
        probability = round(min(max(weighted_sum, 0), 100), 2)

        return RiskAssessment(
            country=signals.country,
            probability_of_escalation=probability,
            risk_level=self._risk_level(probability),
            expected_timeframe_weeks=self._timeframe(probability),
            generated_at=datetime.now(tz=timezone.utc),
        )

    def register_student(self, student: StudentRegistration) -> StudentRegistration:
        self._students[student.student_id] = student
        return student

    def list_students(self, country: str | None = None) -> List[StudentRegistration]:
        students = list(self._students.values())
        if country:
            students = [student for student in students if student.country.lower() == country.lower()]
        return students

    def generate_alert(self, risk: RiskAssessment) -> Alert:
        routes = [
            "Proceed to nearest embassy safe hub",
            "Use daytime movement windows",
        ]
        if risk.risk_level is RiskLevel.high:
            routes.append("Immediate staged evacuation via primary corridor")

        return Alert(
            country=risk.country,
            risk_level=risk.risk_level,
            message=(
                f"{risk.country} risk is {risk.risk_level.value}. "
                f"Escalation probability {risk.probability_of_escalation}%."
            ),
            recommended_exit_routes=routes,
            generated_at=datetime.now(tz=timezone.utc),
        )

    def plan_evacuation(self, request: EvacuationRequest) -> EvacuationPlan:
        network = COUNTRY_NETWORKS.get(request.country)
        if not network:
            raise ValueError(f"No route intelligence available for {request.country}")

        avoid = set(request.avoid_nodes or [])
        route, travel_time, cumulative_risk = self._safest_path(
            network,
            request.origin_city,
            request.target_safe_hub,
            avoid,
        )

        normalized_risk = "Low" if cumulative_risk < 40 else "Medium" if cumulative_risk < 80 else "High"
        return EvacuationPlan(
            route=route,
            estimated_travel_time_hours=round(travel_time, 1),
            risk_score=normalized_risk,
            transport_capacity=request.student_count,
            embassy_contact_point=EMBASSY_CONTACTS.get(request.country, "N/A"),
        )

    @staticmethod
    def _safest_path(
        network: Dict[str, List[Edge]],
        source: str,
        target: str,
        avoid: set[str],
    ) -> Tuple[List[str], float, float]:
        queue: List[Tuple[float, float, str, List[str]]] = [(0.0, 0.0, source, [source])]
        best_cost: Dict[str, float] = {source: 0.0}

        while queue:
            combined_cost, travel_time, node, path = heapq.heappop(queue)
            if node == target:
                cumulative_risk = combined_cost - travel_time
                return path, travel_time, cumulative_risk

            for edge in network.get(node, []):
                if edge.destination in avoid:
                    continue
                next_time = travel_time + edge.travel_time_hours
                next_cost = next_time + edge.risk_penalty
                if next_cost < best_cost.get(edge.destination, float("inf")):
                    best_cost[edge.destination] = next_cost
                    heapq.heappush(
                        queue,
                        (next_cost, next_time, edge.destination, path + [edge.destination]),
                    )

        raise ValueError(f"No safe route found from {source} to {target}")
