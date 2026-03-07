# Geopolitical Conflict Escalation Predictor

This project provides a hackathon-ready baseline that predicts country-level conflict escalation risk and highlights students located in high-risk regions.

## What it includes

- Synthetic conflict-event data inspired by ACLED/UCDP-like fields.
- Monthly feature engineering:
  - protests
  - military events
  - violent conflicts
  - fatalities
  - news sentiment
  - border activity
  - sanctions
  - terror events / social keyword spikes
  - historical conflict index
- RandomForest model that outputs risk score (0 to 1).
- Streamlit dashboard with:
  - top high-risk countries
  - trend charts
  - student distribution and high-risk student list
  - embassy contact table (demo)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
streamlit run streamlit_dashboard.py
```

## Notes on real datasets

To use real data, replace data generation in `streamlit_dashboard.py` with ingestion logic for:

- ACLED (`country`, `event_type`, `fatalities`, `actors`, `date`, `location`)
- UCDP conflict time series
- GDELT/EventRegistry sentiment
- GTD terror incident signals
- Travel advisory risk features

The current setup intentionally uses synthetic data so the dashboard is demo-friendly and fully runnable offline.
