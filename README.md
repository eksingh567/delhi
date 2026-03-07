# SAFEPASS – AI Early Warning & Student Evacuation Intelligence System

This repository now contains a working **MVP backend** for SAFEPASS: an AI-assisted early-warning and evacuation-intelligence platform for students studying abroad.

## What is implemented

- **Conflict risk scoring API** (`/risk/score`) using weighted geopolitical signals.
- **Student safety registry API** (`/students/register`, `/students`) with opt-in fields.
- **Automated alert generation** (`/alerts/generate`) from risk assessments.
- **Evacuation planning engine** (`/evacuation/plan`) that computes a safest path over a country route network.
- **Health endpoint** (`/health`) for operational checks.
- **Unit tests** for core risk, registry, and evacuation logic.

## Architecture (MVP)

- `app/main.py` – FastAPI routes.
- `app/models.py` – Pydantic request/response models.
- `app/services.py` – Risk model + in-memory registry + route optimization.
- `tests/test_services.py` – Unit tests.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open interactive docs at:

- `http://127.0.0.1:8000/docs`

## Example request

```bash
curl -X POST http://127.0.0.1:8000/risk/score \
  -H "Content-Type: application/json" \
  -d '{
    "country": "Ukraine",
    "news_severity": 87,
    "military_activity": 92,
    "diplomatic_tension": 75,
    "economic_sanctions": 68,
    "social_sentiment": 60,
    "historical_pattern": 79
  }'
```

## Next steps to productionize

1. Replace heuristic risk scoring with a trained ML pipeline (NLP + time-series features).
2. Integrate real feeds (news APIs, sanctions feeds, advisories, geospatial conflict layers).
3. Move registry to encrypted persistent storage + strict RBAC + audit trails.
4. Add embassy/university notification channels (email/SMS/secure API).
5. Add parent dashboard and student chatbot.
6. Add safe-zone geospatial indexing and dynamic transport capacity optimization.

## Safety & ethics notes

- Student registry is intended as **opt-in only**.
- Sensitive identity values should be encrypted at rest and in transit.
- AI outputs should be treated as decision support and reviewed by human analysts.
