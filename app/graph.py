import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from . import tools, rules
from .privacy import safe
SERVICE_REGION = os.getenv("SERVICE_REGION", "ALL")  # e.g. "EU" enforces EU-only handling

class S(TypedDict, total=False):
    dispute_id: str; dispute: dict; txn: dict; history: list; merchant: dict
    result: dict; explanation: str; blocked: str; steps: list

def intake(s: S):
    d = tools.get_dispute(s["dispute_id"])
    if not d: return {"blocked": "dispute not found", "steps": ["intake"]}
    if SERVICE_REGION != "ALL" and d["region"] != SERVICE_REGION:   # localization guard
        tools.audit(s["dispute_id"], "blocked_cross_region", {"case": d["region"], "service": SERVICE_REGION})
        return {"blocked": f"Case region {d['region']} cannot be processed in {SERVICE_REGION}", "steps": ["intake"]}
    return {"dispute": d, "steps": ["intake"]}

def gather(s: S):
    t = tools.get_transaction(s["dispute"]["txn_id"])
    h = tools.get_cardholder_history(t["card_token"], t["txn_id"])
    m = tools.get_merchant_profile(t["merchant_id"])
    return {"txn": t, "history": h, "merchant": m, "steps": s["steps"] + ["gather_evidence"]}

def apply_rules(s: S):
    r = rules.triage(s["dispute"], s["txn"], s["history"], s["merchant"])
    tools.audit(s["dispute_id"], "rules_result", r)
    return {"result": r, "steps": s["steps"] + ["apply_rules"]}

def explain(s: S):
    r = s["result"]
    payload = safe({"reason": s["dispute"]["reason"], "claim": s["dispute"]["claim_text"], **r})
    text = f"Recommend {r['action']} ({r['confidence']:.0%}). " + "; ".join(r["evidence"])
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            import anthropic
            msg = anthropic.Anthropic().messages.create(model=os.getenv("MODEL", "claude-sonnet-5-5"), max_tokens=300,
                messages=[{"role": "user", "content": f"Write a 2-sentence analyst-facing explanation of this dispute recommendation. Use only these facts: {payload}"}])
            text = msg.content[0].text
        except Exception as e: text += f" (LLM unavailable: {type(e).__name__})"
    return {"explanation": text, "steps": s["steps"] + ["explain"]}

def route(s: S):
    r = {**s["result"], "route": "human_priority_queue" if s["result"]["priority_review"] else "human_standard_queue"}
    tools.audit(s["dispute_id"], "final_recommendation", r)  # agent recommends; a human decides
    return {"result": r, "steps": s["steps"] + ["route_to_human"]}

g = StateGraph(S)
for n, f in [("intake", intake), ("gather", gather), ("rules", apply_rules), ("explain", explain), ("route", route)]: g.add_node(n, f)
g.set_entry_point("intake")
g.add_conditional_edges("intake", lambda s: END if s.get("blocked") else "gather")
g.add_edge("gather", "rules"); g.add_edge("rules", "explain"); g.add_edge("explain", "route"); g.add_edge("route", END)
graph = g.compile()
