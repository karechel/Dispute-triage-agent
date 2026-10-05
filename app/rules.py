"""Pure, deterministic dispute rules. The LLM never makes the decision."""
from datetime import timedelta
HIGH_VALUE, MIN_CONF = 1000, 0.7

def _home_region(history):
    rs = [h["region"] for h in history]
    return max(set(rs), key=rs.count) if rs else None

def triage(dispute, txn, history, merchant):
    reason, ev = dispute["reason"], []
    if reason == "fraud":
        home = _home_region(history)
        prior = [h for h in history if h["merchant_id"] == txn["merchant_id"]]
        if home and txn["region"] != home:
            ev.append(f"Txn region {txn['region']} differs from usual region {home}")
            if float(merchant["chargeback_rate"]) > 0.05: ev.append("Merchant has high chargeback rate")
            action, conf = "approve", 0.85
        elif len(prior) >= 2:
            ev.append(f"{len(prior)} prior undisputed txns at same merchant (possible friendly fraud)")
            action, conf = "deny", 0.8
        else: action, conf = "escalate", 0.5; ev.append("Inconclusive fraud signals")
    elif reason == "duplicate":
        dup = [h for h in history if h["merchant_id"] == txn["merchant_id"] and h["amount"] == txn["amount"]
               and abs(h["ts"] - txn["ts"]) < timedelta(hours=24)]
        if dup: action, conf = "approve", 0.9; ev.append("Identical txn at same merchant within 24h")
        else: action, conf = "deny", 0.85; ev.append("No matching duplicate found")
    elif reason == "not_received":
        if txn["delivered"] is None: action, conf = "escalate", 0.5; ev.append("Delivery status missing; cannot verify")
        elif txn["delivered"] is False: action, conf = "approve", 0.85; ev.append("Merchant shows no delivery")
        else: action, conf = "deny", 0.75; ev.append("Delivery confirmed by merchant")
    else: action, conf = "escalate", 0.4; ev.append(f"Reason '{reason}' needs manual review")
    needs_human_priority = conf < MIN_CONF or float(txn["amount"]) >= HIGH_VALUE
    return {"action": action, "confidence": conf, "evidence": ev, "priority_review": needs_human_priority}
