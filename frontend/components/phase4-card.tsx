"use client";

import { useState } from "react";

import type { DataGap, InvestorEntry, Phase4Output, Slide } from "@/lib/types";
import { Alert } from "./ui/alert";
import { Spinner } from "./ui/spinner";

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700 border-red-200",
  moderate: "bg-amber-100 text-amber-700 border-amber-200",
  minor: "bg-gray-100 text-gray-600 border-gray-200",
};

function getAgentCardClass(status: string | null | undefined, isActive: boolean) {
  if (isActive) {
    return "border-brand-500 bg-brand-500 text-white shadow-sm";
  }
  if (status === "success") {
    return "border-green-200 bg-green-50 text-green-700";
  }
  if (status === "pending" || status === "skipped") {
    return "border-amber-200 bg-amber-50 text-amber-700";
  }
  return "border-red-200 bg-red-50 text-red-700";
}

function scoreColor(score: number) {
  return score >= 8 ? "text-green-600" : score >= 5 ? "text-amber-600" : "text-red-600";
}

function buildSearchLink(query: string, suffix?: string) {
  const search = suffix ? `${query} ${suffix}` : query;
  return `https://www.google.com/search?q=${encodeURIComponent(search)}`;
}

function buildLinkedInSearchLink(name: string) {
  return `https://www.linkedin.com/search/results/all/?keywords=${encodeURIComponent(name)}`;
}

export function Phase4Card({ output }: { output: Phase4Output }) {
  const [activeTab, setActiveTab] = useState<"decks" | "vc">("decks");
  const [expandedSlide, setExpandedSlide] = useState<number | null>(null);
  const { decks, vc } = output;
  const scorecard = vc?.fundability_scorecard;

  const agents = [
    {
      id: "decks" as const,
      label: "DECKS",
      title: "Investor Deck",
      status: output.agent_statuses?.decks,
      summary: decks?.decks_summary ?? "Narrative arc, slide outline, and data gap review.",
    },
    {
      id: "vc" as const,
      label: "VC",
      title: "Investor Matching",
      status: output.agent_statuses?.vc,
      summary: vc?.vc_summary ?? "Investor targeting, fundability scoring, and outreach sequence.",
    },
  ];

  const activeAgent = agents.find((agent) => agent.id === activeTab) ?? agents[0];

  return (
    <div className="space-y-5 mt-4">
      {output.phase4_status !== "complete" && (
        <Alert variant="success">
          DECKS is ready. VC investor matching is still running in the background and this view will refresh automatically.
        </Alert>
      )}
      {output.mentor_consultation_required && (
        <Alert variant="error">Mentor consultation required - VC agent could not identify sufficient matching investors.</Alert>
      )}
      {output.has_retriggered_data_gap && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-2 text-sm text-amber-800">
          A critical data gap was detected and automatically resolved via a one-time agent re-run.
        </div>
      )}

      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-gray-500">
            Phase 4 Agent Viewer
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">
            {activeAgent.label} <span className="text-gray-400">|</span> {activeAgent.title}
          </h2>
          <p className="mt-1 max-w-2xl text-sm text-gray-600">
            {activeAgent.summary}
          </p>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-2 md:grid-cols-2 max-w-xl">
          {agents.map((agent) => {
            const isActive = agent.id === activeAgent.id;
            return (
              <button
                key={agent.id}
                type="button"
                onClick={() => setActiveTab(agent.id)}
                className={`rounded-xl border px-3 py-3 text-left transition-all ${
                  getAgentCardClass(agent.status, isActive)
                }`}
              >
                <p className="text-sm font-semibold">{agent.label}</p>
                <p className={`text-xs ${isActive ? "text-white/80" : ""}`}>
                  {agent.status ?? "unknown"}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {activeTab === "decks" && decks && (
        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">Deck Readiness</h3>
              <span className={`text-3xl font-bold ${scoreColor(decks.deck_readiness_score ?? 0)}`}>
                {decks.deck_readiness_score ?? "-"}<span className="text-base text-gray-400">/10</span>
              </span>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">{decks.narrative_arc}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h3 className="font-semibold mb-3">12-Slide Outline ({decks.slide_outline?.length ?? 0} slides)</h3>
            <div className="space-y-2">
              {(decks.slide_outline ?? []).map((slide: Slide) => (
                <div key={slide.slide_number} className="border border-gray-100 rounded-xl overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setExpandedSlide(expandedSlide === slide.slide_number ? null : slide.slide_number)}
                    className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center shrink-0">
                        {slide.slide_number}
                      </span>
                      <span className="font-medium text-sm">{slide.title}</span>
                    </div>
                    <span className="text-gray-400 text-xs">{expandedSlide === slide.slide_number ? "▲" : "▼"}</span>
                  </button>
                  {expandedSlide === slide.slide_number && (
                    <div className="px-4 pb-4 border-t border-gray-50">
                      <div className="mt-3 grid sm:grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs font-medium text-gray-500 mb-2">Key Points</p>
                          <ul className="space-y-1">
                            {slide.key_points?.map((point: string, i: number) => (
                              <li key={i} className="text-sm text-gray-700 flex gap-2"><span className="text-indigo-400 shrink-0">*</span>{point}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-gray-500 mb-2">Speaker Notes</p>
                          <p className="text-sm text-gray-600 italic">{slide.speaker_notes}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
          {(decks.data_gaps_identified ?? []).length > 0 && (
            <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
              <h3 className="font-semibold mb-3">Data Gaps</h3>
              <div className="space-y-2">
                {decks.data_gaps_identified.map((gap: DataGap, i: number) => (
                  <div key={i} className={`border rounded-xl px-4 py-3 ${SEVERITY_STYLES[gap.severity] || SEVERITY_STYLES.minor}`}>
                    <p className="text-xs font-medium uppercase tracking-wide mb-1">{gap.severity} · {gap.missing_from_agent}</p>
                    <p className="text-sm">{gap.gap_description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div className="bg-indigo-50 border border-indigo-200 rounded-2xl p-4">
            <p className="text-sm text-indigo-800">{decks.decks_summary}</p>
          </div>
        </div>
      )}

      {activeTab === "vc" && !vc && (
        <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm text-center">
          <Spinner className="text-indigo-500 h-6 w-6 mx-auto mb-3" />
          <p className="text-sm text-gray-600">VC investor matching is still running.</p>
        </div>
      )}

      {activeTab === "vc" && vc && (
        <div className="space-y-4">
          {scorecard && (
            <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
              <h3 className="font-semibold mb-4">Fundability Scorecard</h3>
              <div className="flex items-center gap-4 mb-4">
                <div className="text-center">
                  <p className={`text-4xl font-bold ${scoreColor(scorecard.overall_score)}`}>{scorecard.overall_score}</p>
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
                      <p className={`text-xl font-bold ${scoreColor(score)}`}>{score}</p>
                      <p className="text-xs text-gray-500">{label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h3 className="font-semibold mb-3">Investor List ({vc.investor_list?.length ?? 0})</h3>
            <div className="space-y-3">
              {(vc.investor_list ?? []).map((investor: InvestorEntry) => (
                <div key={investor.priority_rank} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center shrink-0">{investor.priority_rank}</span>
                    <h4 className="font-medium text-sm">{investor.name}</h4>
                    <span className="bg-indigo-100 text-indigo-700 text-xs px-2 py-0.5 rounded-full">{investor.investor_type}</span>
                  </div>
                  <p className="text-sm text-gray-700">{investor.thesis_fit}</p>
                  <p className="text-xs text-gray-500 mt-1"><span className="font-medium">Warm intro:</span> {investor.warm_intro_path}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <a
                      href={buildSearchLink(investor.name, "official website")}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-100 transition-colors"
                    >
                      Website
                    </a>
                    <a
                      href={buildLinkedInSearchLink(investor.name)}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
                    >
                      LinkedIn
                    </a>
                    <a
                      href={buildSearchLink(investor.name, "Crunchbase")}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-100 transition-colors"
                    >
                      Crunchbase
                    </a>
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
