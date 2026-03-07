from __future__ import annotations

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from src.data_generator import (
    generate_conflict_events,
    generate_news_signals,
    generate_social_signals,
    generate_student_data,
)
from src.model_pipeline import build_monthly_features, train_model, top_risk_latest


st.set_page_config(page_title="Global Student Risk Dashboard", layout="wide")
st.title("🌍 Geopolitical Conflict Escalation & Student Risk Dashboard")

with st.spinner("Generating demo datasets and training model..."):
    conflict_df = generate_conflict_events()
    news_df = generate_news_signals(conflict_df)
    social_df = generate_social_signals(news_df)
    students_df = generate_student_data(450)

    feature_df = build_monthly_features(conflict_df, news_df, social_df)
    _model, scored_df, metrics = train_model(feature_df)
    latest_risk = top_risk_latest(scored_df)

st.subheader("Model quality")
col1, col2 = st.columns(2)
col1.metric("ROC-AUC", f"{metrics['roc_auc']:.3f}")
col2.write("Classification report")
col2.code(metrics["report"])

st.subheader("Top High-Risk Countries")
st.dataframe(latest_risk.head(10), width="stretch")

country_risk = latest_risk[["country", "risk_score"]]
student_risk = students_df.merge(country_risk, on="country", how="left")
student_risk["risk_score"] = student_risk["risk_score"].fillna(0.1)
student_risk["risk_level"] = pd.cut(
    student_risk["risk_score"],
    bins=[-0.1, 0.4, 0.7, 1.0],
    labels=["Low", "Medium", "High"],
)

st.subheader("Student distribution by risk level")
summary = (
    student_risk.assign(risk_level=student_risk["risk_level"].astype(str))
    .groupby(["country", "risk_level"], observed=False)["student_id"]
    .count()
    .reset_index(name="student_count")
)
st.dataframe(summary.sort_values(["risk_level", "student_count"], ascending=[True, False]), width="stretch")

st.subheader("Students in high-risk regions")
st.dataframe(student_risk[student_risk["risk_level"] == "High"].head(30), width="stretch")

st.subheader("Conflict trend timeline")
country_pick = st.selectbox("Select country", latest_risk["country"].tolist())
country_trend = scored_df[scored_df["country"] == country_pick].sort_values("month")
fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(country_trend["month"], country_trend["risk_score"], marker="o")
ax.set_title(f"{country_pick} conflict risk over time")
ax.set_xlabel("Month")
ax.set_ylabel("Risk score")
ax.grid(True, alpha=0.3)
st.pyplot(fig)

st.subheader("Embassy contacts (demo)")
embassy_contacts = pd.DataFrame(
    {
        "country": latest_risk["country"],
        "embassy_hotline": [f"+1-202-555-{1000+i}" for i in range(len(latest_risk))],
        "evacuation_priority": latest_risk["escalation_probability"],
    }
)
st.dataframe(embassy_contacts.head(10), width="stretch")
