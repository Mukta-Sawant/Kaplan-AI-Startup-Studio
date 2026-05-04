"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getPhase4Output, runPhase4 } from "@/lib/api";
import type { Phase4Output, Slide, DataGap, InvestorEntry } from "@/lib/types";
import { Spinner } from "@/components/ui/spinner";
import { Alert } from "@/components/ui/alert";

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700 border-red-200",
  moderate: "bg-amber-100 text-amber-700 border-amber-200",
  minor: "bg-gray-100 text-gray-600 border-gray-200",
};

const SCORE_COLOR = (score: number) => {
  if (score >= 8) return "text-green-600";
  if (score >= 5) return "text-amber-600";
  return "text-red-600";
};

export default function Phase4Page() {
  const params = useParams();
  const submissionId = params.id as string;

  const [output, setOutput] = useState<Phase4Output | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"decks" | "vc">("decks");
  const [expandedSlide, setExpandedSlide] = useState<number | null>(null);
  const [rerunning, setRerunning] = useState(false);
  const [rerunError, setRerunError] = useState<string | null>(null);
  const [rerunDone, setRerunDone] = useState(false);

  useEffect(() => {
    getPhase4Output(submissionId)
      .then(setOutput)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [submissionId]);

  async function handleRerun() {
    setRerunning(true);
    setRerunError(null);
    setRerunDone(false);
    try {
      await runPhase4(submissionId);
      const updated = await getPhase4Output(submissionId);
      setOutput(updated);
      setRerunDone(true);
    } catch (e) {
      setRerunError(e instanceof Error ? e.message : "Phase 4 rerun failed.");
    } finally {
      setRerunning(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner className="text-brand-500 h-8 w-8" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-12">
        <Alert variant="error">{error}</Alert>
        <div className="mt-4 flex gap-4">
          <Link href="/dashboard" className="text-brand-600 text-sm underline">Back to Dashboard</Link>
          <Link href={`/phase3/${submissionId}`} className="text-brand-600 text-sm underline">View Phase 3</Link>
        </div>
      </div>
    );
  }

  if (!output) return null;

  const decks = output.decks;
  const vc = output.vc;
  const scorecard = vc?.fundability_scorecard;

  const criticalGaps = (decks?.data_gaps_identified ?? []).filter((g: DataGap) => g.severity === "critical");

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link href="/dashboard" className="text-sm text-gray-500 hover:text-gray-700">
            ← Dashboard
          </Link>
          <h1 className="text-2xl font-bold mt-1">Phase 4 — Moving to Funding</h1>
          <p className="text-xs text-gray-400 mt-0.5">Submission {submissionId}</p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href={`/phase3/${submissionId}`}
            className="text-sm border border-gray-300 text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            View Phase 3
          </Link>
          <button
            onClick={handleRerun}
            disabled={rerunning}
            className="flex items-center gap-2 text-sm border border-indigo-400 text-indigo-600 px-4 py-2 rounded-lg hover:bg-indigo-50 disabled:opacity-60 transition-colors"
          >
            {rerunning && <Spinner className="text-indigo-600 h-4 w-4" />}
            {rerunning ? "Rerunning…" : "↺ Rerun Phase 4"}
          </button>
        </div>
      </div>

      {rerunError && <Alert variant="error" className="mb-4">{rerunError}</Alert>}
      {rerunDone && <Alert variant="success" className="mb-4">Phase 4 rerun complete — results updated.</Alert>}

      {output.mentor_consultation_required && (
        <Alert variant="error" className="mb-4">
          Mentor consultation required — VC agent could not identify sufficient matching investors.
        </Alert>
      )}

      {output.has_retriggered_data_gap && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-2 mb-4 text-sm text-amber-800">
          A critical data gap was detected and automatically resolved via a one-time agent re-run.
        </div>
      )}

      {/* Agent status bar */}
      <div className="bg-white border border-gray-200 rounded-2xl p-4 mb-6 shadow-sm">
        <p className="text-xs font-medium text-gray-500 mb-3 uppercase tracking-wide">Agent Status</p>
        <div className="grid grid-cols-2 gap-2 max-w-xs">
          {(["decks", "vc"] as const).map((agent) => {
            const s = (output.agent_statuses ?? {})[agent];
            return (
              <div key={agent} className={`rounded-xl px-3 py-2 text-center text-xs font-medium ${
                s === "success" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
              }`}>
                {agent.toUpperCase()}
                <br />
                <span className="font-normal">{s ?? "—"}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-xl p-1">
        <button
          onClick={() => setActiveTab("decks")}
          className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
            activeTab === "decks" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
          }`}
        >
          DECKS
          <span className="block text-xs font-normal text-gray-400">Investor Deck</span>
        </button>
        <button
          onClick={() => setActiveTab("vc")}
          className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
            activeTab === "vc" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
          }`}
        >
          VC
          <span className="block text-xs font-normal text-gray-400">Investor Matching</span>
        </button>
      </div>

      {/* DECKS Tab */}
      {activeTab === "decks" && decks && (
        <div className="space-y-6">
          {/* Readiness score + narrative */}
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-lg">Deck Readiness</h2>
              <span className={`text-3xl font-bold ${SCORE_COLOR(decks.deck_readiness_score ?? 0)}`}>
                {decks.deck_readiness_score ?? "—"}<span className="text-base text-gray-400">/10</span>
              </span>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">{decks.narrative_arc}</p>
          </div>

          {/* Critical gaps */}
          {criticalGaps.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
              <h2 className="font-semibold text-lg mb-3">Data Gaps Identified</h2>
              <div className="space-y-2">
                {(decks.data_gaps_identified ?? []).map((gap: DataGap, i: number) => (
                  <div key={i} className={`border rounded-xl px-4 py-3 ${SEVERITY_STYLES[gap.severity] || SEVERITY_STYLES.minor}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium uppercase tracking-wide">{gap.severity}</span>
                      <span className="text-xs">· {gap.missing_from_agent}</span>
                      {gap.trigger_rerun && (
                        <span className="text-xs bg-red-200 text-red-800 px-1.5 py-0.5 rounded">re-run triggered</span>
                      )}
                    </div>
                    <p className="text-sm">{gap.gap_description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Slide outline */}
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h2 className="font-semibold text-lg mb-4">
              12-Slide Outline <span className="text-gray-400 font-normal text-sm">({decks.slide_outline?.length ?? 0} slides)</span>
            </h2>
            <div className="space-y-2">
              {(decks.slide_outline ?? []).map((slide: Slide) => (
                <div key={slide.slide_number} className="border border-gray-100 rounded-xl overflow-hidden">
                  <button
                    onClick={() => setExpandedSlide(expandedSlide === slide.slide_number ? null : slide.slide_number)}
                    className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center shrink-0">
                        {slide.slide_number}
                      </span>
                      <span className="font-medium text-sm">{slide.title}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="hidden sm:flex gap-1">
                        {slide.data_source_agents?.slice(0, 3).map((agent: string) => (
                          <span key={agent} className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">{agent}</span>
                        ))}
                      </div>
                      <span className="text-gray-400 text-xs">{expandedSlide === slide.slide_number ? "▲" : "▼"}</span>
                    </div>
                  </button>
                  {expandedSlide === slide.slide_number && (
                    <div className="px-4 pb-4 border-t border-gray-50">
                      <div className="mt-3 grid sm:grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs font-medium text-gray-500 mb-2">Key Points</p>
                          <ul className="space-y-1">
                            {slide.key_points?.map((pt: string, i: number) => (
                              <li key={i} className="text-sm text-gray-700 flex gap-2">
                                <span className="text-indigo-400 mt-0.5 shrink-0">•</span>{pt}
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-gray-500 mb-2">Speaker Notes</p>
                          <p className="text-sm text-gray-600 italic">{slide.speaker_notes}</p>
                          <p className="text-xs font-medium text-gray-500 mt-3 mb-1">Visual Suggestion</p>
                          <p className="text-sm text-gray-600">{slide.visual_suggestion}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="bg-indigo-50 border border-indigo-200 rounded-2xl p-4">
            <p className="text-sm text-indigo-800">{decks.decks_summary}</p>
          </div>
        </div>
      )}

      {/* VC Tab */}
      {activeTab === "vc" && vc && (
        <div className="space-y-6">
          {/* Fundability Scorecard */}
          {scorecard && (
            <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
              <h2 className="font-semibold text-lg mb-4">Fundability Scorecard</h2>
              <div className="flex items-center gap-4 mb-4">
                <div className="text-center">
                  <p className={`text-4xl font-bold ${SCORE_COLOR(scorecard.overall_score)}`}>
                    {scorecard.overall_score}
                  </p>
                  <p className="text-xs text-gray-500">Overall /10</p>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 flex-1">
                  {[
                    { label: "Team", score: scorecard.team_score },
                    { label: "Market", score: scorecard.market_score },
                    { label: "Traction", score: scorecard.traction_score },
                    { label: "Product", score: scorecard.product_score },
                    { label: "Financial", score: scorecard.financial_score },
                  ].map(({ label, score }) => (
                    <div key={label} className="text-center">
                      <p className={`text-xl font-bold ${SCORE_COLOR(score)}`}>{score}</p>
                      <p className="text-xs text-gray-500">{label}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="space-y-1 mb-3">
                {scorecard.score_breakdown?.map((line: string, i: number) => (
                  <p key={i} className="text-sm text-gray-600 flex gap-2">
                    <span className="text-indigo-400 mt-0.5 shrink-0">•</span>{line}
                  </p>
                ))}
              </div>
              {scorecard.improvement_recommendations?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <p className="text-xs font-medium text-gray-500 mb-2">Improvement Recommendations</p>
                  {scorecard.improvement_recommendations.map((rec: string, i: number) => (
                    <p key={i} className="text-sm text-amber-700 flex gap-2">
                      <span className="mt-0.5 shrink-0">→</span>{rec}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Outreach Strategy */}
          {vc.outreach_strategy && (
            <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
              <h2 className="font-semibold text-lg mb-3">Outreach Strategy</h2>
              <div className="space-y-1 mb-4">
                {vc.outreach_strategy.recommended_sequence?.map((step: string, i: number) => (
                  <p key={i} className="text-sm text-gray-700">{step}</p>
                ))}
              </div>
              <div className="grid sm:grid-cols-2 gap-3">
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">Timing</p>
                  <p className="text-sm text-gray-700">{vc.outreach_strategy.timing_recommendation}</p>
                </div>
                {vc.outreach_strategy.conference_opportunities?.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 mb-1">Conferences</p>
                    <ul className="space-y-0.5">
                      {vc.outreach_strategy.conference_opportunities.map((c: string, i: number) => (
                        <li key={i} className="text-sm text-gray-700">• {c}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Investor List */}
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h2 className="font-semibold text-lg mb-4">
              Investor List <span className="text-gray-400 font-normal text-sm">({vc.investor_list?.length ?? 0} investors)</span>
            </h2>
            <div className="space-y-3">
              {(vc.investor_list ?? []).map((inv: InvestorEntry) => (
                <div key={inv.priority_rank} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center shrink-0">
                          {inv.priority_rank}
                        </span>
                        <h3 className="font-medium text-sm">{inv.name}</h3>
                      </div>
                      <div className="flex flex-wrap gap-1.5 mt-1.5">
                        <span className="bg-indigo-100 text-indigo-700 text-xs px-2 py-0.5 rounded-full">{inv.investor_type}</span>
                        <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">{inv.stage_focus}</span>
                        <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">{inv.fund_size}</span>
                        <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">{inv.geographic_focus}</span>
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-gray-700 mb-2">{inv.thesis_fit}</p>
                  <div className="flex flex-wrap gap-3 text-xs text-gray-500">
                    <span><span className="font-medium">Warm intro:</span> {inv.warm_intro_path}</span>
                    {inv.portfolio_examples?.length > 0 && (
                      <span><span className="font-medium">Portfolio:</span> {inv.portfolio_examples.join(", ")}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-indigo-50 border border-indigo-200 rounded-2xl p-4">
            <p className="text-sm text-indigo-800">{vc.vc_summary}</p>
          </div>
        </div>
      )}
    </div>
  );
}
