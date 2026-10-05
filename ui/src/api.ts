import type { DisputeSummary, TriageResult, Decision } from "./types";
const BASE = "http://localhost:8000";
async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, init);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail ?? `Request failed (${r.status})`);
  return r.json();
}
export const listDisputes = () => call<DisputeSummary[]>("/disputes");
export const triage = (id: string) => call<TriageResult>(`/disputes/${id}/triage`, { method: "POST" });
export const decide = (id: string, d: Decision) =>
  call<{ ok: boolean }>(`/disputes/${id}/decision`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(d) });
