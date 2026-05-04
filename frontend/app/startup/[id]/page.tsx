"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getSubmission,
  getDossier,
  getPhase2Output,
  getPhase3Output,
  getPhase4Output,
  runPhase1,
  runPhase2,
  runPhase3,
  runPhase4,
} from "@/lib/api";
import type {
  SubmissionResponse,
  Dossier,
  Phase2Output,
  Phase3Output,
  Phase4Output,
  CustomerSegment,
  PartnerEntry,
  ChannelTactic,
  Slide,
  DataGap,
  InvestorEntry,
} from "@/lib/types";
import { DossierCard } from "@/components/dossier-card";
import { Phase2Card } from "@/components/phase2-card";
import { Phase3Card } from "@/components/phase3-card";
import { Phase4Card } from "@/components/phase4-card";
import { Spinner } from "@/components/ui/spinner";
import { Alert } from "@/components/ui/alert";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function tryFetch<T>(fn: () => Promise<T>): Promise<T | null> {
  try {
    return await fn();
  } catch {
    return null;
  }
}

const SCORE_COLOR = (score: number) =>
  score >= 8 ? "text-green-600" : score >= 5 ? "text-amber-600" : "text-red-600";

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

// ---------------------------------------------------------------------------
// Phase section wrapper
// ---------------------------------------------------------------------------

function PhaseSection({
  title,
  color,
  badge,
  open,
  onToggle,
  children,
  actions,
}: {
  title: string;
  color: string;
  badge?: React.ReactNode;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  actions?: React.ReactNode;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
      <div
        role="button"
        tabIndex={0}
        onClick={onToggle}
        onKeyDown={(e) => e.key === "Enter" && onToggle()}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-3">
          <span className={`w-2.5 h-2.5 rounded-full ${color}`} />
          <h2 className="text-base font-semibold">{title}</h2>
          {badge}
        </div>
        <div className="flex items-center gap-2">
          {actions}
          <span className="text-gray-400 text-xs ml-2">{open ? "▲" : "▼"}</span>
        </div>
      </div>
      {open && <div className="px-6 pb-6 border-t border-gray-100">{children}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Phase 3 content
// ---------------------------------------------------------------------------

function Phase3Content({ output }: { output: Phase3Output }) {
  const [activeTab, setActiveTab] = useState<"cust" | "channels" | "mktg">("cust");
  const { cust, channels, mktg } = output;

  const tabs = [
    { id: "cust" as const, label: "CUST", sub: "Customer Discovery" },
    { id: "channels" as const, label: "CHANNELS", sub: "Partner Map" },
    { id: "mktg" as const, label: "MKTG", sub: "Marketing Plan" },
  ];

  return (
    <div className="space-y-5 mt-4">
      {output.mentor_intervention_required && (
        <Alert variant="error">
          Mentor intervention required — CUST agent could not identify viable leads after{" "}
          {output.cust_attempts} attempts.
        </Alert>
      )}

      <div className="bg-gray-50 border border-gray-100 rounded-2xl p-3">
        <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Agent Status</p>
        <div className="grid grid-cols-3 gap-2">
          {(["cust", "channels", "mktg"] as const).map((a) => {
            const s = output.agent_statuses?.[a];
            return (
              <div key={a} className={`rounded-xl px-3 py-2 text-center text-xs font-medium ${
                s === "success"
                  ? "bg-green-100 text-green-700"
                  : s === "pending"
                    ? "bg-amber-100 text-amber-700"
                    : "bg-red-100 text-red-700"
              }`}>
                {a.toUpperCase()}<br /><span className="font-normal">{s ?? "—"}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex gap-1 bg-gray-100 rounded-xl p-1">
        {tabs.map((t) => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${activeTab === t.id ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}>
            {t.label}<span className="block text-xs font-normal text-gray-400">{t.sub}</span>
          </button>
        ))}
      </div>

      {activeTab === "cust" && cust && (
        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h3 className="font-semibold mb-2">Early Adopter Profile</h3>
            <p className="text-gray-700 text-sm leading-relaxed">{cust.early_adopter_profile}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h3 className="font-semibold mb-3">Customer Segments ({cust.customer_segments?.length ?? 0})</h3>
            <div className="space-y-3">
              {(cust.customer_segments ?? []).map((seg: CustomerSegment, i: number) => (
                <div key={i} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="bg-orange-100 text-orange-700 text-xs font-medium px-2 py-0.5 rounded-full">Priority {seg.priority_rank}</span>
                    <h4 className="font-medium text-sm">{seg.segment_name}</h4>
                  </div>
                  <p className="text-sm text-gray-600 mb-1"><span className="font-medium">Size:</span> {seg.estimated_segment_size}</p>
                  {seg.pain_points?.length > 0 && (
                    <ul className="space-y-0.5 mt-2">
                      {seg.pain_points.map((p: string, j: number) => (
                        <li key={j} className="text-sm text-gray-600 flex gap-2"><span className="text-orange-400">•</span>{p}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h3 className="font-semibold mb-3">Interview Script Suggestions</h3>
            <ol className="space-y-2">
              {(cust.interview_script_suggestions ?? []).map((q: string, i: number) => (
                <li key={i} className="text-sm text-gray-700 flex gap-3">
                  <span className="text-orange-500 font-medium shrink-0">{i + 1}.</span><span>{q}</span>
                </li>
              ))}
            </ol>
          </div>
          <div className="bg-orange-50 border border-orange-200 rounded-2xl p-4">
            <p className="text-sm text-orange-800">{cust.cust_summary}</p>
          </div>
        </div>
      )}

      {activeTab === "channels" && channels && (
        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h3 className="font-semibold mb-3">Partner Map ({channels.partner_map?.length ?? 0})</h3>
            <div className="space-y-3">
              {(channels.partner_map ?? []).map((p: PartnerEntry, i: number) => (
                <div key={i} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-sm">{p.organization_name}</h4>
                    <div className="flex gap-2">
                      <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full capitalize">{p.partnership_type}</span>
                      <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">Priority {p.outreach_priority}</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">{p.complementary_value}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4">
            <p className="text-sm text-blue-800">{channels.channels_summary}</p>
          </div>
        </div>
      )}

      {activeTab === "mktg" && mktg && (
        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h3 className="font-semibold mb-3">Marketing Plan</h3>
            <div className="space-y-3">
              {(mktg.marketing_plan ?? []).map((t: ChannelTactic, i: number) => (
                <div key={i} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-medium text-sm">{t.channel}</h4>
                    <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">Priority {t.priority}</span>
                  </div>
                  <p className="text-sm text-gray-700 mb-1">{t.tactic}</p>
                  <div className="flex gap-4 text-xs text-gray-500">
                    <span><span className="font-medium">Cost:</span> {t.estimated_cost}</span>
                    <span><span className="font-medium">Reach:</span> {t.expected_reach}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h3 className="font-semibold mb-3">KPI Targets</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(mktg.kpi_targets ?? []).map((kpi, i) => (
                <div key={i} className="border border-gray-100 rounded-xl p-3">
                  <p className="font-medium text-sm">{kpi.metric}</p>
                  <p className="text-xl font-bold text-orange-600 mt-1">{kpi.target_value}</p>
                  <p className="text-xs text-gray-500 mt-1">{kpi.timeframe}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-orange-50 border border-orange-200 rounded-2xl p-4">
            <p className="text-sm text-orange-800">{mktg.mktg_summary}</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Phase 4 content
// ---------------------------------------------------------------------------

function Phase4Content({ output }: { output: Phase4Output }) {
  const [activeTab, setActiveTab] = useState<"decks" | "vc">("decks");
  const [expandedSlide, setExpandedSlide] = useState<number | null>(null);
  const { decks, vc } = output;
  const scorecard = vc?.fundability_scorecard;

  return (
    <div className="space-y-5 mt-4">
      {output.phase4_status !== "complete" && (
        <Alert variant="success">
          DECKS is ready. VC investor matching is still running in the background and this view will refresh automatically.
        </Alert>
      )}
      {output.mentor_consultation_required && (
        <Alert variant="error">Mentor consultation required — VC agent could not identify sufficient matching investors.</Alert>
      )}
      {output.has_retriggered_data_gap && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-2 text-sm text-amber-800">
          A critical data gap was detected and automatically resolved via a one-time agent re-run.
        </div>
      )}

      <div className="bg-gray-50 border border-gray-100 rounded-2xl p-3">
        <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Agent Status</p>
        <div className="grid grid-cols-2 gap-2 max-w-xs">
          {(["decks", "vc"] as const).map((a) => {
            const s = output.agent_statuses?.[a];
            return (
              <div key={a} className={`rounded-xl px-3 py-2 text-center text-xs font-medium ${s === "success" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                {a.toUpperCase()}<br /><span className="font-normal">{s ?? "—"}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex gap-1 bg-gray-100 rounded-xl p-1">
        {(["decks", "vc"] as const).map((t) => (
          <button key={t} onClick={() => setActiveTab(t)}
            className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${activeTab === t ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}>
            {t.toUpperCase()}
            <span className="block text-xs font-normal text-gray-400">{t === "decks" ? "Investor Deck" : "Investor Matching"}</span>
          </button>
        ))}
      </div>

      {activeTab === "decks" && decks && (
        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">Deck Readiness</h3>
              <span className={`text-3xl font-bold ${SCORE_COLOR(decks.deck_readiness_score ?? 0)}`}>
                {decks.deck_readiness_score ?? "—"}<span className="text-base text-gray-400">/10</span>
              </span>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">{decks.narrative_arc}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h3 className="font-semibold mb-3">12-Slide Outline ({decks.slide_outline?.length ?? 0} slides)</h3>
            <div className="space-y-2">
              {(decks.slide_outline ?? []).map((slide: Slide) => (
                <div key={slide.slide_number} className="border border-gray-100 rounded-xl overflow-hidden">
                  <button onClick={() => setExpandedSlide(expandedSlide === slide.slide_number ? null : slide.slide_number)}
                    className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors">
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
                            {slide.key_points?.map((pt: string, i: number) => (
                              <li key={i} className="text-sm text-gray-700 flex gap-2"><span className="text-indigo-400 shrink-0">•</span>{pt}</li>
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
                  <p className={`text-4xl font-bold ${SCORE_COLOR(scorecard.overall_score)}`}>{scorecard.overall_score}</p>
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
            </div>
          )}
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h3 className="font-semibold mb-3">Investor List ({vc.investor_list?.length ?? 0})</h3>
            <div className="space-y-3">
              {(vc.investor_list ?? []).map((inv: InvestorEntry) => (
                <div key={inv.priority_rank} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center shrink-0">{inv.priority_rank}</span>
                    <h4 className="font-medium text-sm">{inv.name}</h4>
                    <span className="bg-indigo-100 text-indigo-700 text-xs px-2 py-0.5 rounded-full">{inv.investor_type}</span>
                  </div>
                  <p className="text-sm text-gray-700">{inv.thesis_fit}</p>
                  <p className="text-xs text-gray-500 mt-1"><span className="font-medium">Warm intro:</span> {inv.warm_intro_path}</p>
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

// ---------------------------------------------------------------------------
// Run button
// ---------------------------------------------------------------------------

function RunPhaseButton({
  label,
  running,
  runningLabel,
  disabled,
  color,
  onClick,
  error,
}: {
  label: string;
  running: boolean;
  runningLabel: string;
  disabled?: boolean;
  color: string;
  onClick: () => void;
  error?: string | null;
}) {
  return (
    <div className="py-6 flex flex-col items-center gap-3">
      {error && <Alert variant="error">{error}</Alert>}
      <button onClick={onClick} disabled={running || disabled}
        className={`flex items-center gap-2 ${color} text-white px-8 py-3 rounded-xl text-sm font-medium disabled:opacity-50 transition-colors`}>
        {running && <Spinner className="text-white h-4 w-4" />}
        {running ? runningLabel : label}
      </button>
      {disabled && !running && (
        <p className="text-xs text-gray-400">Complete the previous phase first.</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function StartupPage() {
  const params = useParams();
  const id = params.id as string;

  const [submission, setSubmission] = useState<SubmissionResponse | null>(null);
  const [dossier, setDossier] = useState<Dossier | null>(null);
  const [phase2, setPhase2] = useState<Phase2Output | null>(null);
  const [phase3, setPhase3] = useState<Phase3Output | null>(null);
  const [phase4, setPhase4] = useState<Phase4Output | null>(null);
  const [loading, setLoading] = useState(true);

  // section open/close
  const [open1, setOpen1] = useState(true);
  const [open2, setOpen2] = useState(true);
  const [open3, setOpen3] = useState(true);
  const [open4, setOpen4] = useState(true);

  // running states
  const [runningP1, setRunningP1] = useState(false);
  const [runningP2, setRunningP2] = useState(false);
  const [runningP3, setRunningP3] = useState(false);
  const [runningP4, setRunningP4] = useState(false);
  const [errorP1, setErrorP1] = useState<string | null>(null);
  const [errorP2, setErrorP2] = useState<string | null>(null);
  const [errorP3, setErrorP3] = useState<string | null>(null);
  const [errorP4, setErrorP4] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      tryFetch(() => getSubmission(id)),
      tryFetch(() => getDossier(id)),
      tryFetch(() => getPhase2Output(id)),
      tryFetch(() => getPhase3Output(id)),
      tryFetch(() => getPhase4Output(id)),
    ]).then(([sub, dos, p2, p3, p4]) => {
      setSubmission(sub);
      setDossier(dos);
      setPhase2(p2);
      setPhase3(p3);
      setPhase4(p4);
      setLoading(false);
    });
  }, [id]);

  useEffect(() => {
    if (!phase4 || phase4.phase4_status === "complete") return;

    const timer = window.setTimeout(async () => {
      try {
        setPhase4(await getPhase4Output(id));
      } catch {
        // keep the current partial output and retry on the next poll cycle
      }
    }, 5000);

    return () => window.clearTimeout(timer);
  }, [id, phase4]);

  async function handleRunP1() {
    setRunningP1(true); setErrorP1(null);
    try {
      await runPhase1(id);
      setDossier(await getDossier(id));
    } catch (e) { setErrorP1(e instanceof Error ? e.message : "Phase 1 failed."); }
    finally { setRunningP1(false); }
  }

  async function handleRunP2() {
    setRunningP2(true); setErrorP2(null);
    try {
      await runPhase2(id);
      setPhase2(await getPhase2Output(id));
      setOpen2(true);
    } catch (e) { setErrorP2(e instanceof Error ? e.message : "Phase 2 failed."); }
    finally { setRunningP2(false); }
  }

  async function handleRunP3() {
    setRunningP3(true); setErrorP3(null);
    try {
      await runPhase3(id);
      setPhase3(await getPhase3Output(id));
      setOpen3(true);
    } catch (e) { setErrorP3(e instanceof Error ? e.message : "Phase 3 failed."); }
    finally { setRunningP3(false); }
  }

  async function handleRunP4() {
    setRunningP4(true); setErrorP4(null);
    try {
      await runPhase4(id);
      setPhase4(await getPhase4Output(id));
      setOpen4(true);
    } catch (e) { setErrorP4(e instanceof Error ? e.message : "Phase 4 failed."); }
    finally { setRunningP4(false); }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner className="text-brand-500 h-8 w-8" />
      </div>
    );
  }

  const phases = [
    { label: "Phase 1", done: !!dossier, color: "bg-green-500" },
    { label: "Phase 2", done: !!phase2, color: "bg-purple-500" },
    { label: "Phase 3", done: !!phase3, color: "bg-orange-500" },
    { label: "Phase 4", done: !!phase4, color: "bg-indigo-500" },
  ];

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <Link href="/dashboard" className="text-sm text-gray-500 hover:text-gray-700">
          ← Dashboard
        </Link>
        <h1 className="text-2xl font-bold mt-1">
          {submission?.startup_name ?? "Startup Analysis"}
        </h1>
        {submission?.one_line_pitch && (
          <p className="text-gray-500 text-sm mt-0.5">{submission.one_line_pitch}</p>
        )}
        <p className="text-xs text-gray-400 mt-1">ID: {id}</p>
      </div>

      {/* Phase progress bar */}
      <div className="flex gap-2 mb-8">
        {phases.map((p) => (
          <div key={p.label} className="flex items-center gap-1.5">
            <span className={`w-2.5 h-2.5 rounded-full ${p.done ? p.color : "bg-gray-200"}`} />
            <span className={`text-xs font-medium ${p.done ? "text-gray-700" : "text-gray-400"}`}>{p.label}</span>
          </div>
        ))}
      </div>

      {/* Sections */}
      <div className="space-y-4">

        {/* Phase 1 */}
        <PhaseSection
          title="Phase 1 — Qualification Dossier"
          color={dossier ? "bg-green-500" : "bg-gray-300"}
          badge={dossier?.mentor_review_required ? (
            <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">Mentor Review Required</span>
          ) : undefined}
          open={open1}
          onToggle={() => setOpen1(!open1)}
          actions={dossier ? (
            <button onClick={(e) => { e.stopPropagation(); handleRunP1(); }} disabled={runningP1}
              className="flex items-center gap-1.5 text-xs border border-brand-400 text-brand-600 px-3 py-1.5 rounded-lg hover:bg-brand-50 disabled:opacity-60 transition-colors">
              {runningP1 && <Spinner className="text-brand-500 h-3 w-3" />}
              {runningP1 ? "Rerunning…" : "↺ Rerun Phase 1"}
            </button>
          ) : undefined}
        >
          {dossier ? (
            <div className="pt-4">
              {errorP1 && <Alert variant="error" className="mb-4">{errorP1}</Alert>}
              <DossierCard dossier={dossier} />
            </div>
          ) : (
            <RunPhaseButton
              label="Run Phase 1"
              running={runningP1}
              runningLabel="Running Phase 1…"
              color="bg-brand-500 hover:bg-brand-600"
              onClick={handleRunP1}
              error={errorP1}
            />
          )}
        </PhaseSection>

        {/* Phase 2 */}
        <PhaseSection
          title="Phase 2 — Stage One Analysis"
          color={phase2 ? "bg-purple-500" : "bg-gray-300"}
          open={open2}
          onToggle={() => setOpen2(!open2)}
          actions={phase2 ? (
            <button onClick={(e) => { e.stopPropagation(); handleRunP2(); }} disabled={runningP2}
              className="flex items-center gap-1.5 text-xs border border-purple-400 text-purple-600 px-3 py-1.5 rounded-lg hover:bg-purple-50 disabled:opacity-60 transition-colors">
              {runningP2 && <Spinner className="text-purple-500 h-3 w-3" />}
              {runningP2 ? "Rerunning…" : "↺ Rerun Phase 2"}
            </button>
          ) : undefined}
        >
          {phase2 ? (
            <div className="pt-4">
              {errorP2 && <Alert variant="error" className="mb-4">{errorP2}</Alert>}
              <Phase2Card output={phase2} />
            </div>
          ) : (
            <RunPhaseButton
              label="Run Phase 2"
              running={runningP2}
              runningLabel="Running 6 agents in parallel…"
              disabled={!dossier}
              color="bg-purple-600 hover:bg-purple-700"
              onClick={handleRunP2}
              error={errorP2}
            />
          )}
        </PhaseSection>

        {/* Phase 3 */}
        <PhaseSection
          title="Phase 3 — Stage Two Engagement"
          color={phase3 ? "bg-orange-500" : "bg-gray-300"}
          open={open3}
          onToggle={() => setOpen3(!open3)}
          actions={phase3 ? (
            <button onClick={(e) => { e.stopPropagation(); handleRunP3(); }} disabled={runningP3}
              className="flex items-center gap-1.5 text-xs border border-orange-400 text-orange-600 px-3 py-1.5 rounded-lg hover:bg-orange-50 disabled:opacity-60 transition-colors">
              {runningP3 && <Spinner className="text-orange-500 h-3 w-3" />}
              {runningP3 ? "Rerunning…" : "↺ Rerun Phase 3"}
            </button>
          ) : undefined}
        >
          {phase3 ? (
            <div className="pt-2">
              {errorP3 && <Alert variant="error" className="mb-4">{errorP3}</Alert>}
              <Phase3Card output={phase3} />
            </div>
          ) : (
            <RunPhaseButton
              label="Run Phase 3"
              running={runningP3}
              runningLabel="Running Phase 3…"
              disabled={!phase2}
              color="bg-orange-500 hover:bg-orange-600"
              onClick={handleRunP3}
              error={errorP3}
            />
          )}
        </PhaseSection>

        {/* Phase 4 */}
        <PhaseSection
          title="Phase 4 — Moving to Funding"
          color={phase4 ? "bg-indigo-500" : "bg-gray-300"}
          open={open4}
          onToggle={() => setOpen4(!open4)}
          actions={phase4 ? (
            <button onClick={(e) => { e.stopPropagation(); handleRunP4(); }} disabled={runningP4}
              className="flex items-center gap-1.5 text-xs border border-indigo-400 text-indigo-600 px-3 py-1.5 rounded-lg hover:bg-indigo-50 disabled:opacity-60 transition-colors">
              {runningP4 && <Spinner className="text-indigo-500 h-3 w-3" />}
              {runningP4 ? "Rerunning…" : "↺ Rerun Phase 4"}
            </button>
          ) : undefined}
        >
          {phase4 ? (
            <div className="pt-2">
              {errorP4 && <Alert variant="error" className="mb-4">{errorP4}</Alert>}
              <Phase4Card output={phase4} />
            </div>
          ) : (
            <RunPhaseButton
              label="Run Phase 4"
              running={runningP4}
              runningLabel="Running Phase 4…"
              disabled={!phase3}
              color="bg-indigo-600 hover:bg-indigo-700"
              onClick={handleRunP4}
              error={errorP4}
            />
          )}
        </PhaseSection>

      </div>
    </div>
  );
}
