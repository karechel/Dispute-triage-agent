from datetime import datetime, timedelta
from app.privacy import mask_text, safe
from app.rules import triage
T0 = datetime(2026, 9, 1)
M = {"chargeback_rate": 0.01}
def tx(**k): return {"txn_id":"t","merchant_id":"M1","amount":50,"ts":T0,"region":"US","delivered":True, **k}

def test_pan_never_in_prompt():
    p = safe({"claim": "my card 4111 1111 1111 1111 was used"})
    assert "4111 1111 1111 1111" not in str(p) and "****1111" in str(p)
def test_mask_plain_text(): assert mask_text("5500000000000004") == "****0004"
def test_foreign_fraud_approved():
    hist = [tx(region="US", merchant_id="M3") for _ in range(3)]
    assert triage({"reason":"fraud"}, tx(region="EU"), hist, M)["action"] == "approve"
def test_friendly_fraud_denied():
    assert triage({"reason":"fraud"}, tx(), [tx() for _ in range(3)], M)["action"] == "deny"
def test_duplicate():
    hist = [tx(ts=T0 - timedelta(minutes=10))]
    assert triage({"reason":"duplicate"}, tx(), hist, M)["action"] == "approve"
    assert triage({"reason":"duplicate"}, tx(), [], M)["action"] == "deny"
def test_not_received(): assert triage({"reason":"not_received"}, tx(delivered=False), [], M)["action"] == "approve"
def test_unknown_escalates_and_high_value_flagged():
    r = triage({"reason":"quality"}, tx(amount=1450), [], M)
    assert r["action"] == "escalate" and r["priority_review"]
def test_missing_delivery_data_escalates():
    assert triage({"reason":"not_received"}, tx(delivered=None), [], M)["action"] == "escalate"
