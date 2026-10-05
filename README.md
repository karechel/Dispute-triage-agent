# Dispute Triage Agent (prototype, synthetic data)
A prototype exploring how agentic AI could assist payments dispute operations. **All data is synthetic.**

## Run
    docker compose up -d && pip install -r requirements.txt
    python db/seed.py
    export ANTHROPIC_API_KEY=...   # optional; falls back to a template explanation
    uvicorn app.main:app --reload   # POST /disputes/D000/triage
    python -m pytest

## Design
LangGraph: intake (region guard) -> gather evidence -> deterministic rules -> LLM explanation -> route to human.
- **Rules decide, LLM explains.** The model never makes the dispute decision; the agent recommends and a human approves.
- **Least privilege:** data tools use a SELECT-only Postgres role, parameterized queries, a statement timeout and a row limit.
- **Privacy:** tokens + last4 only; everything sent to the LLM passes through `privacy.safe` (tested).
- **Localization:** set `SERVICE_REGION=EU` and non-EU cases are blocked (403) and audited.
- **Audit:** every step and the final recommendation is written to `audit_log`.

## At enterprise scale I'd change
Queue-based processing, per-region deployments, a model gateway with cost controls, drift/eval monitoring, real rules service, SSO/RBAC.

## UI (React + TypeScript + Vite)
    cd ui && npm install && npm run dev      # http://localhost:5173 (API on :8000)
Queue -> agent recommendation, confidence, evidence and step trail -> Accept / Override (reason required) / Escalate.
Human decisions are written to `audit_log` via `POST /disputes/{id}/decision`.

## Evals
    python evals/run_evals.py     # 20 labelled disputes, no DB or API key needed; writes evals/RESULTS.md
Covers each reason code plus edge cases: boundary timing (24h), missing data, high value, mixed-region history, prompt injection in claim text.
The first run scored 18/20. It exposed a real bug (missing delivery data was treated as "delivered" and denied), now fixed with a regression test.
One case (E04) remains a known open finding; see `evals/RESULTS.md`.
