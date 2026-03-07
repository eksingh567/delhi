import builtins

import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("numpy")
pytest.importorskip("sklearn")

from src.data_generator import (
    generate_conflict_events,
    generate_news_signals,
    generate_social_signals,
    generate_student_data,
)
from src.model_pipeline import build_monthly_features, train_model


def test_pipeline_end_to_end():
    conflict_df = generate_conflict_events(months=10)
    news_df = generate_news_signals(conflict_df)
    social_df = generate_social_signals(news_df)
    features = build_monthly_features(conflict_df, news_df, social_df)

    assert not features.empty
    assert {"protest_count", "military_events", "conflict_escalation"}.issubset(features.columns)

    _, scored, metrics = train_model(features)
    assert "risk_score" in scored.columns
    assert 0.0 <= metrics["roc_auc"] <= 1.0


def test_generate_student_data_without_faker(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "faker":
            raise ModuleNotFoundError("No module named faker")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    students = generate_student_data(size=10, seed=7)

    assert len(students) == 10
    assert {"student_id", "city", "contact", "emergency_contact"}.issubset(students.columns)
