from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal
from . import tools
from .graph import graph
app = FastAPI(title="Dispute Triage Agent (synthetic data)")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

class Decision(BaseModel):
    decision: Literal["accept", "override", "escalate"]
    final_action: Optional[Literal["approve", "deny"]] = None
    note: Optional[str] = None

@app.post("/disputes/{dispute_id}/decision")
def decide(dispute_id: str, d: Decision):
    if d.decision == "override" and not (d.final_action and d.note):
        raise HTTPException(422, "Override needs a final action and a note")
    tools.audit(dispute_id, "human_decision", d.model_dump())
    return {"ok": True}
@app.get("/disputes")
def disputes(): return tools.list_disputes()
@app.post("/disputes/{dispute_id}/triage")
def triage(dispute_id: str):
    out = graph.invoke({"dispute_id": dispute_id})
    if out.get("blocked"): raise HTTPException(403 if "region" in out["blocked"] else 404, out["blocked"])
    return {"dispute_id": dispute_id, "recommendation": out["result"], "explanation": out["explanation"], "steps": out["steps"]}
