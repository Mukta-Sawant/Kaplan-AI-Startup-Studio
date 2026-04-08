"use client";

import type { Dossier } from "@/lib/types";
import { EvalScoreBadges, TeamScoreBadge } from "./score-badges";
import { ReviewFlag } from "./review-flag";

interface DossierCardProps {
  dossier: Dossier;
}

export function DossierCard({ dossier }: DossierCardProps) {
  const { eval_report, team_report } = dossier;

  return (
    <div className="space-y-8">
      {/* Summary */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-3">Dossier Summary</h2>
        <p className="text-gray-700 text-sm leading-relaxed">
          {dossier.dossier_summary}
        </p>
        <p className="text-xs text-gray-400 mt-3">
          Generated: {new Date(dossier.created_at).toLocaleString()}
        </p>
      </div>

      {/* Review flags */}
      <ReviewFlag
        mentorReviewRequired={dossier.mentor_review_required}
        clarificationRequest={dossier.clarification_request}
      />

      {/* EVAL Report */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4">EVAL Assessment</h2>

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
                  <span className="mt-0.5 shrink-0">●</span>
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
      </div>

      {/* TEAM Report */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4">TEAM Assessment</h2>

        <TeamScoreBadge score={team_report.founder_market_fit_score} />

        {/* Role alignment */}
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
                      — {entry.role}
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
                  <span className="mt-0.5">●</span>
                  <span>{gap}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {team_report.recommended_mentors.length > 0 && (
          <div className="mt-5">
            <h3 className="text-sm font-medium text-gray-600 mb-2">
              Recommended Mentor Specialisations
            </h3>
            <div className="flex flex-wrap gap-2">
              {team_report.recommended_mentors.map((m, i) => (
                <span
                  key={i}
                  className="bg-brand-50 text-brand-700 border border-brand-100 text-xs px-3 py-1 rounded-full"
                >
                  {m}
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
              {team_report.team_risk_factors.map((r, i) => (
                <li key={i} className="text-sm text-yellow-700 flex items-start gap-2">
                  <span className="mt-0.5">▲</span>
                  <span>{r}</span>
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
      </div>
    </div>
  );
}
