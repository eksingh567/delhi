from __future__ import annotations

from datetime import datetime, timezone

from app.models import ClaimCondition, ClaimSubmission, OracleSnapshot
from app.services import GigShieldConsensusEngine


def test_consensus_approves_when_observed_matches(monkeypatch) -> None:
    engine = GigShieldConsensusEngine()

    def fake_snapshot(*args, **kwargs):
        return OracleSnapshot(
            latitude=41.0,
            longitude=-87.0,
            precipitation_mm=8.0,
            wind_speed_kmh=35.0,
            snowfall_cm=0.0,
            observed_condition=ClaimCondition.heavy_rain,
        )

    monkeypatch.setattr(engine, "_build_oracle_snapshot", fake_snapshot)

    decision = engine.process_claim(
        ClaimSubmission(
            driver_id="DRV-100",
            location_query="Chicago, IL",
            claim_start_utc=datetime(2026, 1, 10, 10, tzinfo=timezone.utc),
            claim_end_utc=datetime(2026, 1, 10, 13, tzinfo=timezone.utc),
            claimed_condition=ClaimCondition.heavy_rain,
        )
    )

    assert decision.status.value == "APPROVED"
    assert decision.payout_usd == 15.0


def test_three_strikes_restricts_account(monkeypatch) -> None:
    engine = GigShieldConsensusEngine()

    def fake_snapshot(*args, **kwargs):
        return OracleSnapshot(
            latitude=42.0,
            longitude=-71.0,
            precipitation_mm=0.0,
            wind_speed_kmh=8.0,
            snowfall_cm=0.0,
            observed_condition=ClaimCondition.clear,
        )

    monkeypatch.setattr(engine, "_build_oracle_snapshot", fake_snapshot)

    for _ in range(3):
        decision = engine.process_claim(
            ClaimSubmission(
                driver_id="DRV-220",
                location_query="Boston, MA",
                claim_start_utc=datetime(2026, 1, 12, 8, tzinfo=timezone.utc),
                claim_end_utc=datetime(2026, 1, 12, 10, tzinfo=timezone.utc),
                claimed_condition=ClaimCondition.blizzard,
            )
        )

    assert decision.restricted is True
    assert decision.strikes_after_decision == 3

    denied_after_restriction = engine.process_claim(
        ClaimSubmission(
            driver_id="DRV-220",
            location_query="Boston, MA",
            claim_start_utc=datetime(2026, 1, 13, 8, tzinfo=timezone.utc),
            claim_end_utc=datetime(2026, 1, 13, 10, tzinfo=timezone.utc),
            claimed_condition=ClaimCondition.heavy_rain,
        )
    )
    assert denied_after_restriction.status.value == "DENIED"
    assert denied_after_restriction.payout_usd == 0.0
