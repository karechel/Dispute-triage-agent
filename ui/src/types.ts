export type Action = "approve" | "deny" | "escalate";
export interface DisputeSummary { dispute_id: string; reason: string; region: string }
export interface Recommendation { action: Action; confidence: number; evidence: string[]; priority_review: boolean; route: string }
export interface TriageResult { dispute_id: string; recommendation: Recommendation; explanation: string; steps: string[] }
export type Decision = { decision: "accept" | "escalate" } | { decision: "override"; final_action: "approve" | "deny"; note: string };
