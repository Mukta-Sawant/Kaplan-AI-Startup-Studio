"use client";

import { useState } from "react";

import type { Dossier } from "@/lib/types";
import { EvalScoreBadges, TeamScoreBadge } from "./score-badges";
import { ReviewFlag } from "./review-flag";

interface DossierCardProps {
  dossier: Dossier;
}

type AgentKey = "eval" | "team";

function SectionCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
      <h2 className="text-lg font-semibold mb-4">{title}</h2>
      {children}
    </div>
  );
}

export function DossierCard({ dossier }: DossierCardProps) {
  const { eval_report, team_report } = dossier;
  const hasCoreReports = Boolean(eval_report && team_report);
  const [selectedAgent, setSelectedAgent] = useState<AgentKey>("eval");

  if (!hasCoreReports) {
    return (
      <div className="space-y-8">
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-3">Dossier Summary</h2>
          <p className="text-gray-700 text-sm leading-relaxed">
            {dossier.dossier_summary}
          </p>
          <p className="text-xs text-gray-400 mt-3">
            Generated: {new Date(dossier.created_at).toLocaleString()}
          </p>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-amber-900 mb-2">
            Dossier Format Mismatch
          </h2>
          <p className="text-sm text-amber-800 leading-relaxed">
            This page expects a Phase 1 dossier with EVAL and TEAM reports, but
            the returned payload does not include those sections. Reload the page
            after the backend restarts.
          </p>
        </div>
      </div>
    );
  }

  const agentSections = [
    {
      key: "eval" as const,
      label: "EVAL",
      title: "Idea Evaluation",
      status: "success",
      summary: eval_report.summary_recommendation,
      render: () => (
        <SectionCard title="EVAL Assessment">
          <EvalScoreBadges
            market={eval_report.market_viability_score}
            feasibility={eval_report.feasibility_score}
            scalability={eval_report.scalability_score}
          />

          <div className="mt-5">
            <h3 className="text-sm font-medium text-gray-600 mb-2">
              Summary Recommendation
            </h3>
            <p className="text-gray-800 text-sm leading-relaxed">
              {eval_report.summary_recommendation}
            </p>
          </div>

          {eval_report.red_flags.length > 0 && (
            <div className="mt-5">
              <h3 className="text-sm font-medium text-gray-600 mb-2">
                Red Flags
              </h3>
              <ul className="space-y-1">
                {eval_report.red_flags.map((flag, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-red-700">
                    <span className="mt-0.5 shrink-0">-</span>
                    <span>{flag}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-4 flex items-center gap-2 text-xs text-gray-500">
            <span>Confidence:</span>
            <span className="font-medium">
              {Math.round(eval_report.confidence_level * 100)}%
            </span>
          </div>
        </SectionCard>
      ),
    },
    {
      key: "team" as const,
      label: "TEAM",
      title: "Team Assessment",
      status: "success",
      summary:
        team_report.identified_gaps[0] ??
        "Founder-market fit, role alignment, and mentor recommendations.",
      render: () => (
        <SectionCard title="TEAM Assessment">
          <TeamScoreBadge score={team_report.founder_market_fit_score} />

          {team_report.role_alignment_matrix.length > 0 && (
            <div className="mt-5">
              <h3 className="text-sm font-medium text-gray-600 mb-3">
                Role Alignment
              </h3>
              <div className="space-y-4">
                {team_report.role_alignment_matrix.map((entry, i) => (
                  <div
                    key={i}
                    className="border border-gray-100 rounded-xl p-4 bg-gray-50"
                  >
                    <p className="font-medium text-sm">
                      {entry.member_name}{" "}
                      <span className="text-gray-500 font-normal">
                        - {entry.role}
                      </span>
                    </p>
                    {entry.strengths.length > 0 && (
                      <p className="text-xs text-gray-600 mt-1">
                        <span className="font-medium">Strengths: </span>
                        {entry.strengths.join(", ")}
                      </p>
                    )}
                    {entry.gaps.length > 0 && (
                      <p className="text-xs text-red-600 mt-1">
                        <span className="font-medium">Gaps: </span>
                        {entry.gaps.join(", ")}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {team_report.identified_gaps.length > 0 && (
            <div className="mt-5">
              <h3 className="text-sm font-medium text-gray-600 mb-2">
                Identified Gaps
              </h3>
              <ul className="space-y-1">
                {team_report.identified_gaps.map((gap, i) => (
                  <li key={i} className="text-sm text-orange-700 flex items-start gap-2">
                    <span className="mt-0.5">-</span>
                    <span>{gap}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {team_report.recommended_mentors.length > 0 && (
            <div className="mt-5">
              <h3 className="text-sm font-medium text-gray-600 mb-2">
                Recommended Mentor Specializations
              </h3>
              <div className="flex flex-wrap gap-2">
                {team_report.recommended_mentors.map((mentor, i) => (
                  <span
                    key={i}
                    className="bg-brand-50 text-brand-700 border border-brand-100 text-xs px-3 py-1 rounded-full"
                  >
                    {mentor}
                  </span>
                ))}
              </div>
            </div>
          )}

          {team_report.team_risk_factors.length > 0 && (
            <div className="mt-5">
              <h3 className="text-sm font-medium text-gray-600 mb-2">
                Team Risk Factors
              </h3>
              <ul className="space-y-1">
                {team_report.team_risk_factors.map((risk, i) => (
                  <li key={i} className="text-sm text-yellow-700 flex items-start gap-2">
                    <span className="mt-0.5">^</span>
                    <span>{risk}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-4 flex items-center gap-2 text-xs text-gray-500">
            <span>Confidence:</span>
            <span className="font-medium">
              {Math.round(team_report.confidence_level * 100)}%
            </span>
          </div>
        </SectionCard>
      ),
    },
  ];

  const activeAgent =
    agentSections.find((section) => section.key === selectedAgent) ?? agentSections[0];

  return (
    <div className="space-y-8">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-3">Dossier Summary</h2>
        <p className="text-gray-700 text-sm leading-relaxed">
          {dossier.dossier_summary}
        </p>
        <p className="text-xs text-gray-400 mt-3">
          Generated: {new Date(dossier.created_at).toLocaleString()}
        </p>
      </div>

      <ReviewFlag
        mentorReviewRequired={dossier.mentor_review_required}
        clarificationRequest={dossier.clarification_request}
      />

      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-gray-500">
            Phase 1 Agent Viewer
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">
            {activeAgent.label} <span className="text-gray-400">|</span> {activeAgent.title}
          </h2>
          <p className="mt-1 max-w-2xl text-sm text-gray-600">
            {activeAgent.summary}
          </p>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-2 max-w-xl">
          {agentSections.map((section) => {
            const isActive = section.key === activeAgent.key;
            return (
              <button
                key={section.key}
                type="button"
                onClick={() => setSelectedAgent(section.key)}
                className={`rounded-xl border px-3 py-3 text-left transition-all ${
                  isActive
                    ? "border-brand-500 bg-brand-500 text-white shadow-sm"
                    : "border-green-200 bg-green-50 text-green-700"
                }`}
              >
                <p className="text-sm font-semibold">{section.label}</p>
                <p className={`text-xs ${isActive ? "text-white/80" : ""}`}>
                  {section.status}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {activeAgent.render()}
    </div>
  );
}
