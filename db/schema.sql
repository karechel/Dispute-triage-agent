CREATE TABLE merchants(merchant_id TEXT PRIMARY KEY, name TEXT, category TEXT, country TEXT, chargeback_rate NUMERIC);
CREATE TABLE transactions(txn_id TEXT PRIMARY KEY, card_token TEXT, card_last4 TEXT,
  merchant_id TEXT REFERENCES merchants, amount NUMERIC, currency TEXT DEFAULT 'USD',
  ts TIMESTAMPTZ, region TEXT, channel TEXT, delivered BOOLEAN);
CREATE TABLE disputes(dispute_id TEXT PRIMARY KEY, txn_id TEXT REFERENCES transactions,
  reason TEXT, claim_text TEXT, region TEXT);
CREATE TABLE audit_log(id SERIAL PRIMARY KEY, dispute_id TEXT, event TEXT, payload JSONB, ts TIMESTAMPTZ DEFAULT now());
-- Read-only role used by the agent's data tools (least privilege)
CREATE ROLE analyst_ro LOGIN PASSWORD 'ro';
GRANT SELECT ON merchants, transactions, disputes TO analyst_ro;
