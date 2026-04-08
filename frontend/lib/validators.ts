/**
 * Zod schemas for frontend form validation.
 */

import { z } from "zod";

export const teamMemberSchema = z.object({
  name: z.string().min(1, "Name is required").max(200),
  role: z.string().min(1, "Role is required").max(200),
  resume_text: z.string().min(10, "Please upload a resume or paste at least 10 characters"),
  linkedin_url: z.string().url("Must be a valid LinkedIn URL (e.g. https://linkedin.com/in/yourname)"),
  domain_expertise: z.string().optional(),
  startup_experience: z.string().optional(),
  commitment_level: z.string().optional(),
});

export const submissionSchema = z.object({
  startup_name: z.string().min(1, "Startup name is required").max(255),
  one_line_pitch: z
    .string()
    .min(10, "Pitch must be at least 10 characters")
    .max(500, "Pitch must be under 500 characters"),
  problem_statement: z.string().min(20, "Problem statement must be at least 20 characters"),
  proposed_solution: z.string().min(20, "Proposed solution must be at least 20 characters"),
  target_market: z.string().min(10, "Target market must be at least 10 characters"),
  industry_vertical: z.string().min(1, "Industry vertical is required"),
  business_model: z.string().optional(),
  traction_summary: z.string().optional(),
  competitive_landscape: z.string().optional(),
  technical_status: z.string().optional(),
  stage: z.enum(["idea", "prototype", "MVP", "pilot", "revenue"]),
  supporting_documents: z.array(z.string().url("Must be a valid URL")).optional(),
  team_members: z
    .array(teamMemberSchema)
    .min(1, "At least one team member is required"),
});

export const feedbackSchema = z.object({
  feedback_text: z.string().min(10, "Feedback must be at least 10 characters"),
  source_type: z.enum(["founder", "mentor", "admin"]),
  triggers_rerun: z.boolean(),
  rerun_scope: z.enum(["eval", "team", "phase1"]).optional(),
});

export type SubmissionFormValues = z.infer<typeof submissionSchema>;
export type TeamMemberFormValues = z.infer<typeof teamMemberSchema>;
export type FeedbackFormValues = z.infer<typeof feedbackSchema>;
