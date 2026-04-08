"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { z } from "zod";
import { submissionSchema, type SubmissionFormValues, type TeamMemberFormValues } from "@/lib/validators";
import { createSubmission } from "@/lib/api";
import { TeamMembersForm } from "./team-members-form";
import { Spinner } from "./ui/spinner";
import { Alert } from "./ui/alert";

type FormErrors = Partial<Record<keyof SubmissionFormValues, string>>;

const stages = ["idea", "prototype", "MVP", "pilot", "revenue"] as const;

const INDUSTRY_VERTICALS = [
  // Tech & Software
  "AI / Machine Learning",
  "SaaS / Enterprise Software",
  "Cybersecurity",
  "Cloud Computing / Infrastructure",
  "Developer Tools",
  "Data & Analytics",
  // Health
  "HealthTech / MedTech",
  "Biotech / Life Sciences",
  "Mental Health & Wellness",
  "Pharmaceuticals",
  // Finance
  "FinTech",
  "InsurTech",
  "Blockchain / Web3 / Crypto",
  "Investment & Wealth Management",
  // People & Work
  "HRTech / Future of Work",
  "EdTech / E-Learning",
  "Recruitment & Talent",
  // Commerce & Retail
  "E-Commerce / Retail Tech",
  "Marketplace",
  "Consumer Apps",
  "Advertising / MarTech",
  // Industry & Physical World
  "CleanTech / GreenTech",
  "AgriTech / FoodTech",
  "PropTech / Real Estate",
  "Logistics / Supply Chain",
  "Manufacturing / Industry 4.0",
  "Construction Tech",
  "Mobility / Transportation",
  "Space Tech",
  // Deep Tech & Hardware
  "DeepTech / Advanced Materials",
  "Robotics / Automation",
  "IoT / Connected Devices",
  // Media & Society
  "Media / Content Creation",
  "Gaming / Entertainment",
  "Travel & Hospitality",
  "LegalTech",
  "GovTech / Civic Tech",
  "Social Impact / Non-profit",
  // Other
  "Other",
] as const;

const defaultMember = (): TeamMemberFormValues => ({
  name: "",
  role: "",
  resume_text: "",
  linkedin_url: "",
  domain_expertise: "",
  startup_experience: "",
  commitment_level: "",
});

export function StartupForm() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FormErrors>({});

  const [form, setForm] = useState<SubmissionFormValues>({
    startup_name: "",
    one_line_pitch: "",
    problem_statement: "",
    proposed_solution: "",
    target_market: "",
    industry_vertical: "",
    business_model: "",
    traction_summary: "",
    competitive_landscape: "",
    technical_status: "",
    stage: "idea",
    supporting_documents: [],
    team_members: [defaultMember()],
  });

  function setField<K extends keyof SubmissionFormValues>(
    key: K,
    value: SubmissionFormValues[K]
  ) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setFieldErrors((prev) => ({ ...prev, [key]: undefined }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setFieldErrors({});

    const result = submissionSchema.safeParse(form);
    if (!result.success) {
      const errors: FormErrors = {};
      result.error.errors.forEach((err) => {
        const field = err.path[0] as keyof SubmissionFormValues;
        if (field && !errors[field]) errors[field] = err.message;
      });
      setFieldErrors(errors);
      return;
    }

    setSubmitting(true);
    try {
      const submission = await createSubmission(result.data);
      router.push(`/dashboard?highlight=${submission.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-10">
      {error && <Alert variant="error">{error}</Alert>}

      {/* Section 1: Startup overview */}
      <section>
        <h2 className="text-lg font-semibold mb-4 pb-2 border-b border-gray-200">
          Startup Overview
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <InputField
            label="Startup Name *"
            value={form.startup_name}
            onChange={(v) => setField("startup_name", v)}
            error={fieldErrors.startup_name}
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Stage *
            </label>
            <select
              value={form.stage}
              onChange={(e) => setField("stage", e.target.value as typeof form.stage)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
            >
              {stages.map((s) => (
                <option key={s} value={s}>
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <InputField
              label="One-Line Pitch *"
              value={form.one_line_pitch}
              onChange={(v) => setField("one_line_pitch", v)}
              placeholder="A single sentence describing what you do"
              error={fieldErrors.one_line_pitch}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Industry Vertical *
            </label>
            <select
              value={form.industry_vertical}
              onChange={(e) => setField("industry_vertical", e.target.value)}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white ${
                fieldErrors.industry_vertical ? "border-red-400" : "border-gray-300"
              }`}
            >
              <option value="">Select a sector...</option>
              {INDUSTRY_VERTICALS.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
            {fieldErrors.industry_vertical && (
              <p className="text-xs text-red-500 mt-1">{fieldErrors.industry_vertical}</p>
            )}
          </div>
        </div>
      </section>

      {/* Section 2: Problem & Solution */}
      <section>
        <h2 className="text-lg font-semibold mb-4 pb-2 border-b border-gray-200">
          Problem & Solution
        </h2>
        <div className="space-y-5">
          <TextareaField
            label="Problem Statement *"
            value={form.problem_statement}
            onChange={(v) => setField("problem_statement", v)}
            placeholder="Describe the specific problem you are solving and for whom..."
            rows={4}
            error={fieldErrors.problem_statement}
          />
          <TextareaField
            label="Proposed Solution *"
            value={form.proposed_solution}
            onChange={(v) => setField("proposed_solution", v)}
            placeholder="How does your product or service address the problem?"
            rows={4}
            error={fieldErrors.proposed_solution}
          />
        </div>
      </section>

      {/* Section 3: Market & Business */}
      <section>
        <h2 className="text-lg font-semibold mb-4 pb-2 border-b border-gray-200">
          Market & Business
        </h2>
        <div className="space-y-5">
          <TextareaField
            label="Target Market *"
            value={form.target_market}
            onChange={(v) => setField("target_market", v)}
            placeholder="Who are your customers? How large is the market?"
            rows={3}
            error={fieldErrors.target_market}
          />
          <TextareaField
            label="Business Model"
            value={form.business_model ?? ""}
            onChange={(v) => setField("business_model", v)}
            placeholder="How do you plan to generate revenue?"
            rows={3}
          />
          <TextareaField
            label="Traction Summary"
            value={form.traction_summary ?? ""}
            onChange={(v) => setField("traction_summary", v)}
            placeholder="Any users, pilots, revenue, or partnerships to date?"
            rows={3}
          />
          <TextareaField
            label="Competitive Landscape"
            value={form.competitive_landscape ?? ""}
            onChange={(v) => setField("competitive_landscape", v)}
            placeholder="Who are your competitors and what is your differentiation?"
            rows={3}
          />
          <TextareaField
            label="Technical Status"
            value={form.technical_status ?? ""}
            onChange={(v) => setField("technical_status", v)}
            placeholder="What is the current state of your technology or product?"
            rows={3}
          />
        </div>
      </section>

      {/* Section 4: Team members */}
      <section>
        <h2 className="text-lg font-semibold mb-4 pb-2 border-b border-gray-200">
          Team Members
        </h2>
        {fieldErrors.team_members && (
          <Alert variant="error" className="mb-4">{fieldErrors.team_members}</Alert>
        )}
        <TeamMembersForm
          members={form.team_members}
          onChange={(members) => setField("team_members", members)}
        />
      </section>

      {/* Submit */}
      <div className="pt-4">
        <button
          type="submit"
          disabled={submitting}
          className="flex items-center gap-2 bg-brand-500 text-white px-8 py-3 rounded-xl font-semibold hover:bg-brand-600 disabled:opacity-60 transition-colors"
        >
          {submitting && <Spinner className="text-white" />}
          {submitting ? "Submitting..." : "Submit for Qualification"}
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Reusable field components
// ---------------------------------------------------------------------------

function InputField({
  label,
  value,
  onChange,
  placeholder,
  error,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  error?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 ${
          error ? "border-red-400" : "border-gray-300"
        }`}
      />
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
}

function TextareaField({
  label,
  value,
  onChange,
  placeholder,
  rows = 3,
  error,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  rows?: number;
  error?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className={`w-full rounded-lg border px-3 py-2 text-sm resize-y focus:outline-none focus:ring-2 focus:ring-brand-500 ${
          error ? "border-red-400" : "border-gray-300"
        }`}
      />
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
}
