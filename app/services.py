from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import json
from statistics import mean, pstdev
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from .models import (
    ClaimCondition,
    ClaimDecision,
    ClaimStatus,
    ClaimSubmission,
    DashboardSnapshot,
    DriverForensicState,
    DriverProfile,
    OracleSnapshot,
    PolicyDocument,
    PolicyRule,
)

PAYOUT_PER_HOUR = {
    ClaimCondition.blizzard: 15.0,
    ClaimCondition.heavy_rain: 5.0,
    ClaimCondition.clear: 0.0,
}

CONDITION_SEVERITY = {
    ClaimCondition.clear: 0,
    ClaimCondition.heavy_rain: 1,
    ClaimCondition.blizzard: 2,
}


class GigShieldConsensusEngine:
    def __init__(self) -> None:
        self._drivers: dict[str, DriverForensicState] = {}
        self._claims: list[ClaimDecision] = []
        self._risk_trend: deque[float] = deque(maxlen=30)
        self._seed_driver_registry()

    def _seed_driver_registry(self) -> None:
        for profile in [
            DriverProfile(driver_id="DRV-100", display_name="Avery Quinn", home_base="Chicago, IL"),
            DriverProfile(driver_id="DRV-220", display_name="Samir Patel", home_base="Denver, CO"),
            DriverProfile(driver_id="DRV-340", display_name="Lucia Reyes", home_base="Boston, MA"),
        ]:
            self._drivers[profile.driver_id] = DriverForensicState(
                driver_id=profile.driver_id,
                display_name=profile.display_name,
                strikes=0,
                approved_claims=0,
                denied_claims=0,
                restricted=False,
                forensic_history_score=0.0,
            )

    def process_claim(self, claim: ClaimSubmission) -> ClaimDecision:
        if claim.claim_end_utc <= claim.claim_start_utc:
            raise ValueError("Claim end time must be after start time.")

        driver = self._drivers.get(claim.driver_id)
        if not driver:
            driver = DriverForensicState(
                driver_id=claim.driver_id,
                display_name=claim.driver_id,
                strikes=0,
                approved_claims=0,
                denied_claims=0,
                restricted=False,
                forensic_history_score=0.0,
            )
            self._drivers[claim.driver_id] = driver

        oracle = self._build_oracle_snapshot(claim.location_query, claim.claim_start_utc, claim.claim_end_utc)
        claim_hours = (claim.claim_end_utc - claim.claim_start_utc).total_seconds() / 3600
        approved_hours = max(0.0, round(claim_hours, 2))

        claimed_rank = CONDITION_SEVERITY[claim.claimed_condition]
        observed_rank = CONDITION_SEVERITY[oracle.observed_condition]
        is_consensus_pass = claimed_rank <= observed_rank and observed_rank > 0

        if driver.restricted:
            status = ClaimStatus.denied
            approved_hours = 0
            payout = 0.0
            reason = "Account restricted after 3 failed forensic consensus checks."
            driver.denied_claims += 1
        elif is_consensus_pass:
            status = ClaimStatus.approved
            payout = round(PAYOUT_PER_HOUR[oracle.observed_condition] * approved_hours, 2)
            reason = f"Consensus verified {oracle.observed_condition.value.lower()} conditions."
            driver.approved_claims += 1
        else:
            status = ClaimStatus.denied
            approved_hours = 0
            payout = 0.0
            driver.strikes += 1
            driver.denied_claims += 1
            reason = f"Claim severity exceeded oracle conditions. Strike {driver.strikes}/3 recorded."
            if driver.strikes >= 3:
                driver.restricted = True
                reason += " Account now restricted pending manual investigation."

        total_claims = driver.approved_claims + driver.denied_claims
        driver.forensic_history_score = round((driver.strikes / max(total_claims, 1)) * 100, 2)

        decision = ClaimDecision(
            claim_id=f"CLM-{uuid4().hex[:10].upper()}",
            driver_id=claim.driver_id,
            status=status,
            approved_hours=approved_hours,
            payout_usd=payout,
            reason=reason,
            strikes_after_decision=driver.strikes,
            restricted=driver.restricted,
            oracle=oracle,
            processed_at=datetime.now(tz=timezone.utc),
        )
        self._claims.append(decision)
        self._risk_trend.append(self.dashboard_snapshot().real_time_risk_score)
        return decision

    def _http_json(self, url: str, headers: dict[str, str] | None = None) -> Any:
        req = Request(url, headers=headers or {})
        with urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    def _build_oracle_snapshot(self, location_query: str, start_utc: datetime, end_utc: datetime) -> OracleSnapshot:
        lat, lon = self._geocode_location(location_query)
        precip, wind, snowfall = self._query_weather_window(lat, lon, start_utc, end_utc)

        if snowfall >= 2.0 or wind >= 45:
            observed = ClaimCondition.blizzard
        elif precip >= 4.0 or wind >= 30:
            observed = ClaimCondition.heavy_rain
        else:
            observed = ClaimCondition.clear

        return OracleSnapshot(
            latitude=lat,
            longitude=lon,
            precipitation_mm=round(precip, 2),
            wind_speed_kmh=round(wind, 2),
            snowfall_cm=round(snowfall, 2),
            observed_condition=observed,
        )

    def _geocode_location(self, location_query: str) -> tuple[float, float]:
        url = f"https://nominatim.openstreetmap.org/search?{urlencode({'q': location_query, 'format': 'jsonv2', 'limit': 1})}"
        payload = self._http_json(url, headers={"User-Agent": "GigShield-Forensic-Auditor/1.0"})
        if not payload:
            raise ValueError("Location could not be resolved by Nominatim.")
        return float(payload[0]["lat"]), float(payload[0]["lon"])

    def _query_weather_window(self, lat: float, lon: float, start_utc: datetime, end_utc: datetime) -> tuple[float, float, float]:
        params = urlencode(
            {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_utc.date().isoformat(),
                "end_date": end_utc.date().isoformat(),
                "hourly": "precipitation,wind_speed_10m,snowfall",
                "timezone": "UTC",
            }
        )
        payload = self._http_json(f"https://archive-api.open-meteo.com/v1/archive?{params}")

        hourly = payload.get("hourly", {})
        times = hourly.get("time", [])
        precipitation = hourly.get("precipitation", [])
        wind = hourly.get("wind_speed_10m", [])
        snowfall = hourly.get("snowfall", [])

        selected_precip, selected_wind, selected_snow = [], [], []
        for idx, stamp in enumerate(times):
            moment = datetime.fromisoformat(stamp).replace(tzinfo=timezone.utc)
            if start_utc <= moment <= end_utc:
                selected_precip.append(float(precipitation[idx]))
                selected_wind.append(float(wind[idx]))
                selected_snow.append(float(snowfall[idx]))

        if not selected_precip:
            selected_precip = [float(x) for x in precipitation] or [0.0]
            selected_wind = [float(x) for x in wind] or [0.0]
            selected_snow = [float(x) for x in snowfall] or [0.0]

        return max(selected_precip), max(selected_wind), max(selected_snow)

    def dashboard_snapshot(self) -> DashboardSnapshot:
        if not self._claims:
            return DashboardSnapshot(
                generated_at=datetime.now(tz=timezone.utc),
                total_claims=0,
                approval_rate=0.0,
                local_volatility=0.0,
                traffic_density=0.0,
                forensic_history_risk=0.0,
                real_time_risk_score=0.0,
                risk_trend=[0.0],
                payout_exposure_usd=0.0,
            )

        approvals = sum(1 for c in self._claims if c.status is ClaimStatus.approved)
        approval_rate = approvals / len(self._claims) * 100
        wind_values = [c.oracle.wind_speed_kmh for c in self._claims]
        precip_values = [c.oracle.precipitation_mm for c in self._claims]
        volatility = min(100.0, pstdev(wind_values) + pstdev(precip_values) * 3.5)
        heavy_claims = [c for c in self._claims if c.oracle.observed_condition is not ClaimCondition.clear]
        traffic_density = min(100.0, (len(heavy_claims) / len(self._claims)) * 100)
        forensic_history = mean(d.forensic_history_score for d in self._drivers.values())
        risk = min(100.0, max(0.0, 0.4 * volatility + 0.35 * traffic_density + 0.25 * forensic_history))

        return DashboardSnapshot(
            generated_at=datetime.now(tz=timezone.utc),
            total_claims=len(self._claims),
            approval_rate=round(approval_rate, 2),
            local_volatility=round(volatility, 2),
            traffic_density=round(traffic_density, 2),
            forensic_history_risk=round(forensic_history, 2),
            real_time_risk_score=round(risk, 2),
            risk_trend=(list(self._risk_trend) + [round(risk, 2)])[-20:],
            payout_exposure_usd=round(sum(c.payout_usd for c in self._claims), 2),
        )

    def list_drivers(self) -> list[DriverForensicState]:
        return sorted(self._drivers.values(), key=lambda d: d.driver_id)

    def recent_claims(self) -> list[ClaimDecision]:
        return list(reversed(self._claims[-50:]))

    def policy_document(self) -> PolicyDocument:
        return PolicyDocument(
            generated_at=datetime.now(tz=timezone.utc),
            payout_rules={k.value: v for k, v in PAYOUT_PER_HOUR.items()},
            strike_policy=[
                PolicyRule(title="Strike 1", detail="Failed consensus denies payout and records strike."),
                PolicyRule(title="Strike 2", detail="Second strike escalates account into enhanced monitoring."),
                PolicyRule(title="Strike 3", detail="Third strike restricts account and blocks new payouts."),
            ],
            consensus_description=[
                PolicyRule(title="Oracle Resolution", detail="Nominatim resolves claim location into coordinates."),
                PolicyRule(title="Historical Validation", detail="Open-Meteo archive validates precipitation, wind, and snowfall during claim window."),
                PolicyRule(title="Severity Consensus", detail="Claimed severity must not exceed observed oracle severity."),
            ],
        )
