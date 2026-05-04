/**
 * Typed API client for the KI Agentic System FastAPI backend.
 *
 * All requests go through the `apiFetch` helper which reads the base URL
 * from the NEXT_PUBLIC_API_BASE_URL environment variable.
 */

import type {
  AgentRunSummary,
  Dossier,
  FeedbackCreate,
  FeedbackResponse,
  Phase2Output,
  Phase2Summary,
  Phase3Output,
  Phase3Summary,
  Phase4Output,
  Phase4Summary,
  SubmissionCreate,
  SubmissionListItem,
  SubmissionResponse,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}/api${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore parse error
    }
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Submission endpoints
// ---------------------------------------------------------------------------

export async function createSubmission(
  payload: SubmissionCreate
): Promise<SubmissionResponse> {
  return apiFetch<SubmissionResponse>("/submissions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getSubmission(id: string): Promise<SubmissionResponse> {
  return apiFetch<SubmissionResponse>(`/submissions/${id}`);
}

export async function listSubmissions(
  skip = 0,
  limit = 50
): Promise<SubmissionListItem[]> {
  return apiFetch<SubmissionListItem[]>(
    `/submissions?skip=${skip}&limit=${limit}`
  );
}

// ---------------------------------------------------------------------------
// Combined submit + Phase 1
// ---------------------------------------------------------------------------

export async function submitAndEvaluate(payload: SubmissionCreate): Promise<{
  message: string;
  submission_id: string;
  phase_output_id: string;
  mentor_review_required: boolean;
  phase1_status: string;
  dossier: Dossier;
}> {
  return apiFetch("/submit", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// Phase 1 endpoints
// ---------------------------------------------------------------------------

export async function runPhase1(submissionId: string): Promise<{
  message: string;
  submission_id: string;
  phase_output_id: string;
  mentor_review_required: boolean;
  phase1_status: string;
}> {
  return apiFetch(`/phase1/run/${submissionId}`, { method: "POST" });
}

export async function getDossier(submissionId: string): Promise<Dossier> {
  return apiFetch<Dossier>(`/dossier/${submissionId}`);
}

// ---------------------------------------------------------------------------
// Agent runs
// ---------------------------------------------------------------------------

export async function listAgentRuns(
  submissionId: string
): Promise<AgentRunSummary[]> {
  return apiFetch<AgentRunSummary[]>(`/agent-runs/${submissionId}`);
}

// ---------------------------------------------------------------------------
// Feedback
// ---------------------------------------------------------------------------

export async function submitFeedback(
  payload: FeedbackCreate
): Promise<FeedbackResponse> {
  return apiFetch<FeedbackResponse>("/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// Resume upload
// ---------------------------------------------------------------------------

export async function uploadResume(
  file: File
): Promise<{ text: string; filename: string }> {
  const form = new FormData();
  form.append("file", file);
  const url = `${BASE_URL}/api/upload/resume`;
  const res = await fetch(url, { method: "POST", body: form });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Phase 2 endpoints
// ---------------------------------------------------------------------------

export async function runPhase2(submissionId: string): Promise<{
  message: string;
  submission_id: string;
  phase_output_id: string;
  phase2_status: string;
  agent_statuses: Record<string, string>;
}> {
  return apiFetch(`/phase2/run/${submissionId}`, { method: "POST" });
}

export async function getPhase2Output(submissionId: string): Promise<Phase2Output> {
  return apiFetch<Phase2Output>(`/phase2/output/${submissionId}`);
}

export async function getPhase2Summary(submissionId: string): Promise<Phase2Summary> {
  return apiFetch<Phase2Summary>(`/phase2/summary/${submissionId}`);
}

// ---------------------------------------------------------------------------
// Phase 3 endpoints
// ---------------------------------------------------------------------------

export async function runPhase3(submissionId: string): Promise<{
  message: string;
  submission_id: string;
  phase_output_id: string;
  phase3_status: string;
  agent_statuses: Record<string, string>;
  mentor_intervention_required: boolean;
  cust_attempts: number;
}> {
  return apiFetch(`/phase3/run/${submissionId}`, { method: "POST" });
}

export async function getPhase3Output(submissionId: string): Promise<Phase3Output> {
  return apiFetch<Phase3Output>(`/phase3/output/${submissionId}`);
}

export async function getPhase3Summary(submissionId: string): Promise<Phase3Summary> {
  return apiFetch<Phase3Summary>(`/phase3/summary/${submissionId}`);
}

// ---------------------------------------------------------------------------
// Phase 4 endpoints
// ---------------------------------------------------------------------------

export async function runPhase4(submissionId: string): Promise<{
  message: string;
  submission_id: string;
  phase_output_id: string;
  phase4_status: string;
  agent_statuses: Record<string, string>;
  has_retriggered_data_gap: boolean;
  mentor_consultation_required: boolean;
}> {
  return apiFetch(`/phase4/run/${submissionId}`, { method: "POST" });
}

export async function getPhase4Output(submissionId: string): Promise<Phase4Output> {
  return apiFetch<Phase4Output>(`/phase4/output/${submissionId}`);
}

export async function getPhase4Summary(submissionId: string): Promise<Phase4Summary> {
  return apiFetch<Phase4Summary>(`/phase4/summary/${submissionId}`);
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export async function healthCheck(): Promise<{ status: string }> {
  return apiFetch<{ status: string }>("/health");
}
