import { useEffect, useState } from "react";
import { listDisputes, triage, decide } from "./api";
import type { DisputeSummary, TriageResult } from "./types";

const LABEL: Record<string, string> = { fraud: "Fraud", duplicate: "Duplicate charge", not_received: "Item not received", quality: "Quality" };
const STEPS: Record<string, string> = { intake: "Checked case region", gather_evidence: "Pulled transaction, history, merchant", apply_rules: "Applied dispute rules", explain: "Wrote explanation", route_to_human: "Queued for analyst" };

export default function App() {
  const [list, setList] = useState<DisputeSummary[]>([]);
  const [sel, setSel] = useState<string | null>(null);
  const [res, setRes] = useState<TriageResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<Record<string, string>>({});
  const [overriding, setOverriding] = useState(false);
  const [finalAction, setFinalAction] = useState<"approve" | "deny">("approve");
  const [note, setNote] = useState("");

  useEffect(() => { listDisputes().then(setList).catch(e => setErr(e.message)); }, []);

  // Re-run triage whenever the analyst selects a different dispute; ignore stale responses.
  useEffect(() => {
    if (!sel) return;
    let stale = false;
    setBusy(true); setRes(null); setErr(null); setOverriding(false); setNote("");
    triage(sel).then(r => !stale && setRes(r)).catch(e => !stale && setErr(e.message)).finally(() => !stale && setBusy(false));
    return () => { stale = true; };
  }, [sel]);

  async function submit(label: string, body: Parameters<typeof decide>[1]) {
    if (!sel) return;
    try { await decide(sel, body); setDone(d => ({ ...d, [sel]: label })); setOverriding(false); }
    catch (e) { setErr((e as Error).message); }
  }

  const rec = res?.recommendation;
  return (
    <div className="shell">
      <aside className="queue" aria-label="Dispute queue">
        <h1>Disputes</h1>
        <p className="muted">Synthetic data. The agent recommends; you decide.</p>
        <ul>{list.map(d => (
          <li key={d.dispute_id}>
            <button className={d.dispute_id === sel ? "row active" : "row"} onClick={() => setSel(d.dispute_id)}>
              <span className="id">{d.dispute_id}</span><span>{LABEL[d.reason] ?? d.reason}</span>
              <span className="muted">{done[d.dispute_id] ? `Done: ${done[d.dispute_id]}` : d.region}</span>
            </button>
          </li>))}
        </ul>
      </aside>

      <main className="detail">
        {err && <p role="alert" className="error">{err}</p>}
        {!sel && <p className="empty">Select a dispute to see the agent's recommendation.</p>}
        {busy && <p className="muted">Agent is reviewing the case…</p>}
        {rec && res && (<>
          <header>
            <h2>{sel} · {LABEL[list.find(d => d.dispute_id === sel)?.reason ?? ""] ?? "Dispute"}</h2>
            {rec.priority_review && <span className="flag">Priority review</span>}
          </header>
          <section className={`verdict ${rec.action}`}>
            <div><span className="muted">Recommendation</span><strong>{rec.action}</strong></div>
            <div className="meter" role="img" aria-label={`Confidence ${Math.round(rec.confidence * 100)} percent`}>
              <div style={{ width: `${rec.confidence * 100}%` }} /><span>{Math.round(rec.confidence * 100)}% confident</span>
            </div>
          </section>
          <p>{res.explanation}</p>
          <h3>Evidence</h3><ul className="plain">{rec.evidence.map(e => <li key={e}>{e}</li>)}</ul>
          <h3>What the agent did</h3>
          <ol className="trail">{res.steps.map(s => <li key={s}>{STEPS[s] ?? s}</li>)}</ol>

          {done[sel!] ? <p className="ok">Decision recorded: {done[sel!]}.</p> : (
            <div className="actions">
              <button className="primary" onClick={() => submit("accepted", { decision: "accept" })}>Accept recommendation</button>
              <button onClick={() => setOverriding(o => !o)}>Override</button>
              <button onClick={() => submit("escalated", { decision: "escalate" })}>Escalate</button>
              {overriding && (
                <div className="override">
                  <label>Final action
                    <select value={finalAction} onChange={e => setFinalAction(e.target.value as "approve" | "deny")}>
                      <option value="approve">Approve</option><option value="deny">Deny</option></select></label>
                  <label>Reason for override
                    <textarea value={note} onChange={e => setNote(e.target.value)} rows={3} /></label>
                  <button className="primary" disabled={!note.trim()}
                    onClick={() => submit(`overridden to ${finalAction}`, { decision: "override", final_action: finalAction, note })}>Confirm override</button>
                </div>)}
            </div>)}
        </>)}
      </main>
    </div>);
}
