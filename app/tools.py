"""Data tools. Connect as read-only role, parameterized SQL only, timeout + row limit."""
import os, json, psycopg
from psycopg.rows import dict_row
RO = os.getenv("RO_DSN", "postgresql://analyst_ro:ro@localhost:5432/disputes?options=-c%20statement_timeout%3D3000")
RW = os.getenv("ADMIN_DSN", "postgresql://postgres:postgres@localhost:5432/disputes")
def _q(sql, args=()):
    assert sql.lstrip().upper().startswith("SELECT") and ";" not in sql  # single SELECT only
    with psycopg.connect(RO, row_factory=dict_row) as c: return c.execute(sql + " LIMIT 200", args).fetchall()
def get_dispute(did): r = _q("SELECT * FROM disputes WHERE dispute_id=%s", (did,)); return r[0] if r else None
def get_transaction(tid): r = _q("SELECT * FROM transactions WHERE txn_id=%s", (tid,)); return r[0] if r else None
def get_cardholder_history(tok, exclude): return _q("SELECT * FROM transactions WHERE card_token=%s AND txn_id<>%s ORDER BY ts DESC", (tok, exclude))
def get_merchant_profile(mid): r = _q("SELECT * FROM merchants WHERE merchant_id=%s", (mid,)); return r[0] if r else None
def list_disputes(): return _q("SELECT dispute_id, reason, region FROM disputes ORDER BY dispute_id")
def audit(did, event, payload):
    with psycopg.connect(RW, autocommit=True) as c:
        c.execute("INSERT INTO audit_log(dispute_id,event,payload) VALUES (%s,%s,%s)", (did, event, json.dumps(payload, default=str)))
