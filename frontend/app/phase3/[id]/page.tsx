"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getPhase3Output, runPhase3 } from "@/lib/api";
import type { Phase3Output, CustomerSegment, PartnerEntry, ChannelTactic } from "@/lib/types";
import { Spinner } from "@/components/ui/spinner";
import { Alert } from "@/components/ui/alert";

export default function Phase3Page() {
  const params = useParams();
  const submissionId = params.id as string;

  const [output, setOutput] = useState<Phase3Output | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"cust" | "channels" | "mktg">("cust");
  const [rerunning, setRerunning] = useState(false);
  const [rerunError, setRerunError] = useState<string | null>(null);
  const [rerunDone, setRerunDone] = useState(false);

  useEffect(() => {
    getPhase3Output(submissionId)
      .then(setOutput)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [submissionId]);

  async function handleRerun() {
    setRerunning(true);
    setRerunError(null);
    setRerunDone(false);
    try {
      await runPhase3(submissionId);
      const updated = await getPhase3Output(submissionId);
      setOutput(updated);
      setRerunDone(true);
    } catch (e) {
      setRerunError(e instanceof Error ? e.message : "Phase 3 rerun failed.");
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
          <Link href={`/phase2/${submissionId}`} className="text-brand-600 text-sm underline">View Phase 2</Link>
        </div>
      </div>
    );
  }

  if (!output) return null;

  const cust = output.cust;
  const channels = output.channels;
  const mktg = output.mktg;

  const tabs = [
    { id: "cust" as const, label: "CUST", sublabel: "Customer Discovery" },
    { id: "channels" as const, label: "CHANNELS", sublabel: "Partner Map" },
    { id: "mktg" as const, label: "MKTG", sublabel: "Marketing Plan" },
  ];

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link href="/dashboard" className="text-sm text-gray-500 hover:text-gray-700">
            ← Dashboard
          </Link>
          <h1 className="text-2xl font-bold mt-1">Phase 3 — Stage Two Engagement</h1>
          <p className="text-xs text-gray-400 mt-0.5">Submission {submissionId}</p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href={`/phase2/${submissionId}`}
            className="text-sm border border-gray-300 text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            View Phase 2
          </Link>
          <button
            onClick={handleRerun}
            disabled={rerunning}
            className="flex items-center gap-2 text-sm border border-orange-400 text-orange-600 px-4 py-2 rounded-lg hover:bg-orange-50 disabled:opacity-60 transition-colors"
          >
            {rerunning && <Spinner className="text-orange-500 h-4 w-4" />}
            {rerunning ? "Rerunning…" : "↺ Rerun Phase 3"}
          </button>
          <Link
            href={`/phase4/${submissionId}`}
            className="text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            View Phase 4
          </Link>
        </div>
      </div>

      {rerunError && <Alert variant="error" className="mb-4">{rerunError}</Alert>}
      {rerunDone && <Alert variant="success" className="mb-4">Phase 3 rerun complete — results updated.</Alert>}

      {output.mentor_intervention_required && (
        <Alert variant="error" className="mb-6">
          Mentor intervention required — CUST agent could not identify viable leads after {output.cust_attempts} attempts.
        </Alert>
      )}

      {/* Agent status bar */}
      <div className="bg-white border border-gray-200 rounded-2xl p-4 mb-6 shadow-sm">
        <p className="text-xs font-medium text-gray-500 mb-3 uppercase tracking-wide">Agent Status</p>
        <div className="grid grid-cols-3 gap-2">
          {(["cust", "channels", "mktg"] as const).map((agent) => {
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
        {(output.cust_attempts ?? 1) > 1 && (
          <p className="text-xs text-amber-600 mt-2">CUST required {output.cust_attempts} attempts.</p>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-xl p-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label}
            <span className="block text-xs font-normal text-gray-400">{tab.sublabel}</span>
          </button>
        ))}
      </div>

      {/* CUST Tab */}
      {activeTab === "cust" && cust && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h2 className="font-semibold text-lg mb-2">Early Adopter Profile</h2>
            <p className="text-gray-700 text-sm leading-relaxed">{cust.early_adopter_profile}</p>
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h2 className="font-semibold text-lg mb-4">
              Customer Segments <span className="text-gray-400 font-normal text-sm">({cust.customer_segments?.length ?? 0})</span>
            </h2>
            <div className="space-y-4">
              {(cust.customer_segments ?? []).map((seg: CustomerSegment, i: number) => (
                <div key={i} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="bg-orange-100 text-orange-700 text-xs font-medium px-2 py-0.5 rounded-full">
                      Priority {seg.priority_rank}
                    </span>
                    <h3 className="font-medium">{seg.segment_name}</h3>
                  </div>
                  <p className="text-sm text-gray-600 mb-1"><span className="font-medium">Professional:</span> {seg.professional_profile}</p>
                  <p className="text-sm text-gray-600 mb-2"><span className="font-medium">Size:</span> {seg.estimated_segment_size}</p>
                  {seg.pain_points?.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-500 mb-1">Pain Points</p>
                      <ul className="space-y-0.5">
                        {seg.pain_points.map((p: string, j: number) => (
                          <li key={j} className="text-sm text-gray-600 flex gap-2">
                            <span className="text-orange-400 mt-0.5">•</span>{p}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h2 className="font-semibold text-lg mb-4">
              Outreach Targets <span className="text-gray-400 font-normal text-sm">({cust.outreach_list?.length ?? 0})</span>
            </h2>
            <div className="space-y-3">
              {(cust.outreach_list ?? []).map((t, i) => (
                <div key={i} className="border border-gray-100 rounded-xl p-4">
                  <p className="font-medium text-sm">{t.target_type}</p>
                  <p className="text-sm text-gray-600 mt-1">{t.profile_description}</p>
                  <div className="flex gap-4 mt-2 text-xs text-gray-500">
                    <span><span className="font-medium">Find via:</span> {t.discovery_channel}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h2 className="font-semibold text-lg mb-3">Interview Script Suggestions</h2>
            <ol className="space-y-2">
              {(cust.interview_script_suggestions ?? []).map((q: string, i: number) => (
                <li key={i} className="text-sm text-gray-700 flex gap-3">
                  <span className="text-orange-500 font-medium shrink-0">{i + 1}.</span>
                  <span>{q}</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="bg-orange-50 border border-orange-200 rounded-2xl p-4">
            <p className="text-sm text-orange-800">{cust.cust_summary}</p>
          </div>
        </div>
      )}

      {/* CHANNELS Tab */}
      {activeTab === "channels" && channels && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h2 className="font-semibold text-lg mb-4">
              Partner Map <span className="text-gray-400 font-normal text-sm">({channels.partner_map?.length ?? 0} partners)</span>
            </h2>

            {Object.keys(channels.partnership_types_breakdown ?? {}).length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {Object.entries(channels.partnership_types_breakdown ?? {}).map(([type, count]) => (
                  <span key={type} className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full capitalize">
                    {type}: {count as number}
                  </span>
                ))}
              </div>
            )}

            <div className="space-y-3">
              {(channels.partner_map ?? []).map((p: PartnerEntry, i: number) => (
                <div key={i} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-sm">{p.organization_name}</h3>
                    <div className="flex gap-2">
                      <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full capitalize">{p.partnership_type}</span>
                      <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">Priority {p.outreach_priority}</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600"><span className="font-medium">Shared audience:</span> {p.shared_audience}</p>
                  <p className="text-sm text-gray-600 mt-1">{p.complementary_value}</p>
                </div>
              ))}
            </div>
          </div>

          {(channels.partnership_gaps ?? []).length > 0 && (
            <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
              <h2 className="font-semibold text-lg mb-3">Partnership Gaps</h2>
              <ul className="space-y-2">
                {channels.partnership_gaps.map((gap: string, i: number) => (
                  <li key={i} className="text-sm text-gray-600 flex gap-2">
                    <span className="text-amber-500 mt-0.5">⚠</span>{gap}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4">
            <p className="text-sm text-blue-800">{channels.channels_summary}</p>
          </div>
        </div>
      )}

      {/* MKTG Tab */}
      {activeTab === "mktg" && mktg && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h2 className="font-semibold text-lg mb-4">Marketing Plan</h2>
            <div className="space-y-3">
              {(mktg.marketing_plan ?? []).map((tactic: ChannelTactic, i: number) => (
                <div key={i} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-sm">{tactic.channel}</h3>
                    <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">Priority {tactic.priority}</span>
                  </div>
                  <p className="text-sm text-gray-700 mb-2">{tactic.tactic}</p>
                  <div className="flex gap-4 text-xs text-gray-500">
                    <span><span className="font-medium">Cost:</span> {tactic.estimated_cost}</span>
                    <span><span className="font-medium">Reach:</span> {tactic.expected_reach}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h2 className="font-semibold text-lg mb-4">8-Week Content Calendar</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-2 pr-4 text-xs font-medium text-gray-500">Week</th>
                    <th className="text-left py-2 pr-4 text-xs font-medium text-gray-500">Theme</th>
                    <th className="text-left py-2 pr-4 text-xs font-medium text-gray-500">Type</th>
                    <th className="text-left py-2 text-xs font-medium text-gray-500">CTA</th>
                  </tr>
                </thead>
                <tbody>
                  {(mktg.content_calendar ?? []).map((week, i) => (
                    <tr key={i} className="border-b border-gray-50">
                      <td className="py-2 pr-4 font-medium text-gray-700">W{week.week}</td>
                      <td className="py-2 pr-4 text-gray-600">{week.theme}</td>
                      <td className="py-2 pr-4">
                        <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">{week.content_type}</span>
                      </td>
                      <td className="py-2 text-gray-600 text-xs">{week.call_to_action}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h2 className="font-semibold text-lg mb-4">KPI Targets</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(mktg.kpi_targets ?? []).map((kpi, i) => (
                <div key={i} className="border border-gray-100 rounded-xl p-3">
                  <p className="font-medium text-sm">{kpi.metric}</p>
                  <p className="text-xl font-bold text-orange-600 mt-1">{kpi.target_value}</p>
                  <p className="text-xs text-gray-500 mt-1">{kpi.timeframe} · {kpi.measurement_method}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h2 className="font-semibold text-lg mb-4">Messaging Templates</h2>
            <div className="space-y-4">
              {(mktg.messaging_templates ?? []).map((tmpl, i) => (
                <div key={i} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="bg-purple-100 text-purple-700 text-xs px-2 py-0.5 rounded-full">{tmpl.channel}</span>
                    <h3 className="font-medium text-sm">{tmpl.template_name}</h3>
                  </div>
                  <p className="text-xs font-medium text-gray-500 mb-1">Subject / Opener</p>
                  <p className="text-sm text-gray-700 mb-2 italic">"{tmpl.subject_or_opener}"</p>
                  <p className="text-xs font-medium text-gray-500 mb-1">Body</p>
                  <p className="text-sm text-gray-600 whitespace-pre-wrap">{tmpl.body}</p>
                  <p className="text-xs text-brand-600 mt-2 font-medium">CTA: {tmpl.call_to_action}</p>
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
