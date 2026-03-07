from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from .models import (
    Alert,
    EvacuationPlan,
    EvacuationRequest,
    GeopoliticalSignals,
    RiskAssessment,
    StudentRegistration,
)
from .services import SafePassEngine

app = FastAPI(
    title="SAFEPASS API",
    description="AI early-warning and student evacuation intelligence prototype",
    version="0.1.0",
)

engine = SafePassEngine()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/risk/score", response_model=RiskAssessment)
def risk_score(signals: GeopoliticalSignals) -> RiskAssessment:
    return engine.assess_risk(signals)


@app.post("/students/register", response_model=StudentRegistration)
def register_student(student: StudentRegistration) -> StudentRegistration:
    return engine.register_student(student)


@app.get("/students", response_model=list[StudentRegistration])
def list_students(country: str | None = Query(default=None)) -> list[StudentRegistration]:
    return engine.list_students(country)


@app.post("/alerts/generate", response_model=Alert)
def generate_alert(signals: GeopoliticalSignals) -> Alert:
    risk = engine.assess_risk(signals)
    return engine.generate_alert(risk)


@app.post("/evacuation/plan", response_model=EvacuationPlan)
def evacuation_plan(request: EvacuationRequest) -> EvacuationPlan:
    try:
        return engine.plan_evacuation(request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
