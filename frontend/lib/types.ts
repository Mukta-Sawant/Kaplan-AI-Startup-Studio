/**
 * Shared TypeScript types mirroring backend Pydantic schemas.
 */

// ---------------------------------------------------------------------------
// Submission
// ---------------------------------------------------------------------------

export type StartupStage = "idea" | "prototype" | "MVP" | "pilot" | "revenue";
export type SubmissionStatus =
  | "submitted"
  | "clarification_needed"
  | "phase1_complete"
  | "mentor_review_required";

export interface TeamMemberInput {
  name: string;
  role: string;
  resume_text: string;
  linkedin_url: string;
  domain_expertise?: string;
  startup_experience?: string;
  commitment_level?: string;
}

export interface SubmissionCreate {
  startup_name: string;
  one_line_pitch: string;
  problem_statement: string;
  proposed_solution: string;
  target_market: string;
  industry_vertical: string;
  business_model?: string;
  traction_summary?: string;
  competitive_landscape?: string;
  technical_status?: string;
  stage: StartupStage;
  supporting_documents?: string[];
  team_members: TeamMemberInput[];
}

export interface SubmissionResponse extends SubmissionCreate {
  id: string;
  status: SubmissionStatus;
  created_at: string;
  updated_at: string;
}

export interface SubmissionListItem {
  id: string;
  startup_name: string;
  one_line_pitch: string;
  stage: StartupStage;
  status: SubmissionStatus;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Agent runs
// ---------------------------------------------------------------------------

export interface AgentRunSummary {
  id: string;
  agent_name: string;
  model_name: string;
  version: string;
  system_prompt_version: string;
  run_status: "success" | "failed" | "clarification_needed";
  coherence_score: number | null;
  confidence_level: number | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Dossier
// ---------------------------------------------------------------------------

export interface RoleAlignmentEntry {
  member_name: string;
  role: string;
  strengths: string[];
  coverage_areas: string[];
  gaps: string[];
}

export interface EvalReport {
  market_viability_score: number;
  feasibility_score: number;
  scalability_score: number;
  red_flags: string[];
  summary_recommendation: string;
  confidence_level: number;
  clarification_request: string | null;
}

export interface TeamReport {
  role_alignment_matrix: RoleAlignmentEntry[];
  founder_market_fit_score: number;
  identified_gaps: string[];
  recommended_mentors: string[];
  team_risk_factors: string[];
  confidence_level: number;
}

export interface Dossier {
  submission_id: string;
  phase: string;
  eval_report: EvalReport;
  team_report: TeamReport;
  mentor_review_required: boolean;
  dossier_summary: string;
  created_at: string;
  phase1_status?: string;
  clarification_request?: string | null;
}

// ---------------------------------------------------------------------------
// Feedback
// ---------------------------------------------------------------------------

export type FeedbackSource = "founder" | "mentor" | "admin";
export type RerunScope = "eval" | "team" | "phase1";

export interface FeedbackCreate {
  submission_id: string;
  source_type: FeedbackSource;
  feedback_text: string;
  triggers_rerun: boolean;
  rerun_scope?: RerunScope;
}

export interface FeedbackResponse extends FeedbackCreate {
  id: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// API errors
// ---------------------------------------------------------------------------

export interface ApiError {
  detail: string;
  code?: string;
}
