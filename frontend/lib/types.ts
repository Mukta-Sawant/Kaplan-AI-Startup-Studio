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
  | "mentor_review_required"
  | "phase2_complete";

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

// ---------------------------------------------------------------------------
// Phase 2 — Stage One Analysis
// ---------------------------------------------------------------------------

export interface ClarificationQuestion {
  question: string;
  rationale: string;
  topic_area: string;
  priority: number;
}

export interface InteractReport {
  clarification_questions: ClarificationQuestion[];
  priority_topics: string[];
  information_gaps: string[];
  recommended_follow_up_areas: string[];
  interaction_summary: string;
  confidence_level: number;
  clarification_request?: string | null;
}

export interface MarketSegment {
  segment_name: string;
  estimated_size: string;
  growth_potential: string;
  accessibility: string;
}

export interface DiscoveryReport {
  total_addressable_market: string;
  serviceable_addressable_market: string;
  serviceable_obtainable_market: string;
  market_growth_rate: string;
  key_market_trends: string[];
  market_segments: MarketSegment[];
  regulatory_landscape: string;
  industry_maturity: string;
  market_entry_barriers: string[];
  market_opportunities: string[];
  market_threats: string[];
  discovery_summary: string;
  confidence_level: number;
  clarification_request?: string | null;
}

export interface Competitor {
  name: string;
  type: string;
  strengths: string[];
  weaknesses: string[];
  market_share_estimate: string;
  threat_level: string;
}

export interface CompReport {
  direct_competitors: Competitor[];
  indirect_competitors: Competitor[];
  competitive_advantages: string[];
  competitive_disadvantages: string[];
  differentiation_factors: string[];
  moat_assessment: string;
  competitive_positioning: string;
  white_space_opportunities: string[];
  competitive_risk_factors: string[];
  overall_competitive_score: number;
  comp_summary: string;
  confidence_level: number;
  clarification_request?: string | null;
}

export interface RiskItem {
  risk_id: string;
  category: string;
  description: string;
  probability: string;
  impact: string;
  mitigation_strategy: string;
  residual_risk: string;
}

export interface RiskReport {
  risk_register: RiskItem[];
  overall_risk_score: number;
  critical_risks: string[];
  market_risks: string[];
  technical_risks: string[];
  regulatory_risks: string[];
  financial_risks: string[];
  operational_risks: string[];
  risk_mitigation_summary: string;
  go_no_go_recommendation: string;
  confidence_level: number;
  clarification_request?: string | null;
}

export interface MarketingChannel {
  channel: string;
  strategy: string;
  estimated_cost: string;
  expected_reach: string;
  priority: number;
}

export interface GTMReport {
  primary_target_segments: string[];
  ideal_customer_profile: string;
  value_proposition: string;
  pricing_model: string;
  pricing_strategy: string;
  marketing_channels: MarketingChannel[];
  sales_strategy: string;
  launch_timeline: string;
  key_partnerships: string[];
  customer_acquisition_strategy: string;
  gtm_risk_factors: string[];
  success_metrics: string[];
  gtm_summary: string;
  confidence_level: number;
  clarification_request?: string | null;
}

export interface YearlyProjection {
  year: number;
  revenue: string;
  gross_margin: string;
  operating_expenses: string;
  ebitda: string;
  headcount: number;
}

export interface UnitEconomics {
  customer_acquisition_cost: string;
  lifetime_value: string;
  ltv_cac_ratio: string;
  payback_period_months: number;
  gross_margin_percent: string;
}

export interface FinReport {
  revenue_projections: YearlyProjection[];
  burn_rate_monthly: string;
  runway_months: number;
  funding_ask: string;
  pre_money_valuation: string;
  use_of_funds: string[];
  unit_economics: UnitEconomics;
  key_financial_assumptions: string[];
  financial_risk_factors: string[];
  break_even_timeline: string;
  investment_readiness_score: number;
  fin_summary: string;
  confidence_level: number;
  clarification_request?: string | null;
}

export interface Phase2AgentStatuses {
  interact: "success" | "failed";
  discovery: "success" | "failed";
  comp: "success" | "failed";
  risk: "success" | "failed";
  gtm: "success" | "failed";
  fin: "success" | "failed";
}

export interface Phase2Output {
  phase2_status: string;
  submission_id: string;
  interact: InteractReport | null;
  discovery: DiscoveryReport | null;
  comp: CompReport | null;
  risk: RiskReport | null;
  gtm: GTMReport | null;
  fin: FinReport | null;
  agent_statuses: Phase2AgentStatuses;
}

export interface Phase2Summary {
  submission_id: string;
  phase2_status: string;
  agent_statuses: Phase2AgentStatuses;
  summary: {
    interact: {
      question_count: number;
      priority_topics: string[];
      confidence_level: number | null;
    };
    discovery: {
      tam: string | null;
      market_growth_rate: string | null;
      industry_maturity: string | null;
      confidence_level: number | null;
      summary: string | null;
    };
    comp: {
      overall_competitive_score: number | null;
      direct_competitor_count: number;
      confidence_level: number | null;
      summary: string | null;
    };
    risk: {
      overall_risk_score: number | null;
      risk_count: number;
      go_no_go: string | null;
      confidence_level: number | null;
      summary: string | null;
    };
    gtm: {
      pricing_model: string | null;
      primary_segments: string[];
      confidence_level: number | null;
      summary: string | null;
    };
    fin: {
      investment_readiness_score: number | null;
      funding_ask: string | null;
      runway_months: number | null;
      confidence_level: number | null;
      summary: string | null;
    };
  };
}
