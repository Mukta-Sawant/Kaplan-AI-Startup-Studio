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
  SubmissionCreate,
  SubmissionListItem,
  SubmissionResponse,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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
// Health
// ---------------------------------------------------------------------------

export async function healthCheck(): Promise<{ status: string }> {
  return apiFetch<{ status: string }>("/health");
}
