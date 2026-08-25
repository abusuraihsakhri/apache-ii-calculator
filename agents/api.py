"""
FastAPI REST API Server for Apache Ii Calculator.
"""
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor
from ..enrichment import apache_enrichment

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Apache Ii Calculator API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "apache-ii-calculator", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


class WeaningRequest(BaseModel):
    apache_score: int
    acute_physiology: int
    resp_subscore: int
    rsbi: float
    nif: float
    sbt_pass: bool = False
    ventilator_days: int = 0


@app.post("/api/weaning")
def api_weaning(req: WeaningRequest):
    result = apache_enrichment.weaning.assess(
        apache_score=req.apache_score, acute_physiology=req.acute_physiology,
        resp_subscore=req.resp_subscore, rsbi=req.rsbi, nif=req.nif,
        sbt_pass=req.sbt_pass, ventilator_days=req.ventilator_days,
    )
    return {
        "weaning_readiness_index": result.weaning_readiness_index,
        "risk_level": result.risk_level,
        "rsbi_status": result.rsbi_status,
        "nif_status": result.nif_status,
        "sbt_status": result.sbt_status,
        "ventilator_free_days_estimate": result.ventilator_free_days_estimate,
        "tracheostomy_discussion": result.tracheostomy_discussion,
        "recommendation": result.recommendation,
    }


class FluidRequest(BaseModel):
    apache_score: int
    map_value: float
    hr: int
    ppv: Optional[float] = None
    svv: Optional[float] = None
    plr_co_change: Optional[float] = None


@app.post("/api/fluid")
def api_fluid(req: FluidRequest):
    result = apache_enrichment.fluid.assess(
        apache_score=req.apache_score, map_value=req.map_value, hr=req.hr,
        ppv=req.ppv, svv=req.svv, plr_co_change=req.plr_co_change,
    )
    return {
        "fluid_responsive": result.fluid_responsive,
        "probability": result.probability,
        "map_status": result.map_status,
        "apache_circulatory_severity": result.apache_circulatory_severity,
        "bolus_vs_vasopressor": result.bolus_vs_vasopressor,
        "caution_level": result.caution_level,
        "recommendation": result.recommendation,
    }


class RRTRequest(BaseModel):
    apache_score: int
    apache_prev: int
    hours: int = 24
    patient_id: str = "ICU-001"
    ph: float = 7.4
    pao2: float = 100
    creatinine: float = 1.0
    gcs: int = 15


@app.post("/api/rrt")
def api_rrt(req: RRTRequest):
    result = apache_enrichment.rrt.assess(
        apache_score=req.apache_score, apache_prev=req.apache_prev,
        hours=req.hours, patient_id=req.patient_id,
        ph=req.ph, pao2=req.pao2, creatinine=req.creatinine, gcs=req.gcs,
    )
    return {
        "rrt_activated": result.rrt_activated,
        "trigger_reasons": result.trigger_reasons,
        "apache_trajectory": result.apache_trajectory,
        "predicted_mortality_impact": result.predicted_mortality_impact,
        "sbar_alert": result.sbar_alert,
    }
