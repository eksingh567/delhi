from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import ClaimSubmission, DashboardSnapshot, PolicyDocument
from .services import GigShieldConsensusEngine

app = FastAPI(
    title="GigShield AI Forensic Auditor",
    description="Level 0 production forensic consensus and payout platform for gig workers",
    version="1.0.0",
)

engine = GigShieldConsensusEngine()

BASE_DIR = Path(__file__).resolve().parent
PAGES_DIR = BASE_DIR / "pages"
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def index_page() -> FileResponse:
    return FileResponse(PAGES_DIR / "index.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard_page() -> FileResponse:
    return FileResponse(PAGES_DIR / "dashboard.html")


@app.get("/claims", include_in_schema=False)
def claims_page() -> FileResponse:
    return FileResponse(PAGES_DIR / "claims.html")


@app.get("/policy", include_in_schema=False)
def policy_page() -> FileResponse:
    return FileResponse(PAGES_DIR / "policy.html")


@app.get("/api/dashboard", response_model=DashboardSnapshot)
def dashboard_data() -> DashboardSnapshot:
    return engine.dashboard_snapshot()


@app.get("/api/drivers")
def driver_data():
    return engine.list_drivers()


@app.get("/api/claims")
def claim_feed():
    return engine.recent_claims()


@app.post("/api/claims/submit")
def submit_claim(claim: ClaimSubmission):
    try:
        return engine.process_claim(claim)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/policy", response_model=PolicyDocument)
def policy_data() -> PolicyDocument:
    return engine.policy_document()
