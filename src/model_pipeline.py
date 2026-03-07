from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split


def build_monthly_features(conflict_df: pd.DataFrame, news_df: pd.DataFrame, social_df: pd.DataFrame) -> pd.DataFrame:
    conflict = conflict_df.copy()
    conflict["month"] = pd.to_datetime(conflict["date"]).dt.to_period("M").dt.to_timestamp()

    features = (
        conflict.groupby(["country", "month"], as_index=False)
        .agg(
            protest_count=("event_type", lambda s: (s == "Protest").sum()),
            military_events=("event_type", lambda s: (s == "Battles").sum()),
            violent_conflicts=("event_type", lambda s: (s.isin(["Battles", "Violence against civilians"]).sum())),
            fatalities=("fatalities", "sum"),
        )
        .merge(news_df, on=["country", "month"], how="left")
        .merge(social_df, on=["country", "month"], how="left")
        .sort_values(["country", "month"])
    )

    features["historical_conflict_index"] = (
        features.groupby("country")["violent_conflicts"].rolling(3, min_periods=1).mean().reset_index(level=0, drop=True)
    )
    features["next_month_violent"] = features.groupby("country")["violent_conflicts"].shift(-1)
    threshold = features["violent_conflicts"].quantile(0.65)
    features["conflict_escalation"] = (features["next_month_violent"] > threshold).astype(int)
    return features.dropna(subset=["next_month_violent"]).reset_index(drop=True)


def train_model(feature_df: pd.DataFrame) -> tuple[RandomForestClassifier, pd.DataFrame, dict]:
    feature_cols = [
        "protest_count",
        "military_events",
        "violent_conflicts",
        "fatalities",
        "news_sentiment",
        "border_activity",
        "sanctions",
        "terror_events",
        "keyword_spike",
        "historical_conflict_index",
    ]
    X = feature_df[feature_cols]
    y = feature_df["conflict_escalation"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=7, stratify=y)
    model = RandomForestClassifier(n_estimators=350, random_state=7, class_weight="balanced")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "roc_auc": roc_auc_score(y_test, y_proba),
        "report": classification_report(y_test, y_pred, output_dict=False),
    }

    scored = feature_df.copy()
    scored["risk_score"] = model.predict_proba(X)[:, 1]
    return model, scored, metrics


def top_risk_latest(scored_df: pd.DataFrame) -> pd.DataFrame:
    latest_month = scored_df["month"].max()
    latest = scored_df[scored_df["month"] == latest_month].copy()
    latest = latest.sort_values("risk_score", ascending=False)
    latest["escalation_probability"] = np.where(latest["risk_score"] > 0.7, "HIGH", np.where(latest["risk_score"] > 0.4, "MEDIUM", "LOW"))
    return latest[["country", "month", "risk_score", "escalation_probability"]]
