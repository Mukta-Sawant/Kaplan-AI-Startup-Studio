"use client";

import { useState } from "react";

import type { ChannelTactic, CustomerSegment, PartnerEntry, Phase3Output } from "@/lib/types";
import { Alert } from "./ui/alert";

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

export function Phase3Card({ output }: { output: Phase3Output }) {
  const [activeTab, setActiveTab] = useState<"cust" | "channels" | "mktg">("cust");
  const { cust, channels, mktg } = output;

  const agents = [
    {
      id: "cust" as const,
      label: "CUST",
      title: "Customer Discovery",
      status: output.agent_statuses?.cust,
      summary: cust?.cust_summary ?? "Customer segments, outreach targets, and interview guidance.",
    },
    {
      id: "channels" as const,
      label: "CHANNELS",
      title: "Partner Map",
      status: output.agent_statuses?.channels,
      summary: channels?.channels_summary ?? "Partner categories, anchor opportunities, and outreach paths.",
    },
    {
      id: "mktg" as const,
      label: "MKTG",
      title: "Marketing Plan",
      status: output.agent_statuses?.mktg,
      summary: mktg?.mktg_summary ?? "Marketing channels, KPIs, and 12-month activation plan.",
    },
  ];

  const activeAgent = agents.find((agent) => agent.id === activeTab) ?? agents[0];

  return (
    <div className="space-y-5 mt-4">
      {output.mentor_intervention_required && (
        <Alert variant="error">
          Mentor intervention required - CUST agent could not identify viable leads after{" "}
          {output.cust_attempts} attempts.
        </Alert>
      )}

      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-gray-500">
            Phase 3 Agent Viewer
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">
            {activeAgent.label} <span className="text-gray-400">|</span> {activeAgent.title}
          </h2>
          <p className="mt-1 max-w-2xl text-sm text-gray-600">
            {activeAgent.summary}
          </p>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-2 md:grid-cols-3">
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
                      {seg.pain_points.map((point: string, j: number) => (
                        <li key={j} className="text-sm text-gray-600 flex gap-2"><span className="text-orange-400">*</span>{point}</li>
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
              {(cust.interview_script_suggestions ?? []).map((question: string, i: number) => (
                <li key={i} className="text-sm text-gray-700 flex gap-3">
                  <span className="text-orange-500 font-medium shrink-0">{i + 1}.</span><span>{question}</span>
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
              {(channels.partner_map ?? []).map((partner: PartnerEntry, i: number) => (
                <div key={i} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-sm">{partner.organization_name}</h4>
                    <div className="flex gap-2">
                      <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full capitalize">{partner.partnership_type}</span>
                      <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">Priority {partner.outreach_priority}</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">{partner.complementary_value}</p>
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
              {(mktg.marketing_plan ?? []).map((tactic: ChannelTactic, i: number) => (
                <div key={i} className="border border-gray-100 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-medium text-sm">{tactic.channel}</h4>
                    <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">Priority {tactic.priority}</span>
                  </div>
                  <p className="text-sm text-gray-700 mb-1">{tactic.tactic}</p>
                  <div className="flex gap-4 text-xs text-gray-500">
                    <span><span className="font-medium">Cost:</span> {tactic.estimated_cost}</span>
                    <span><span className="font-medium">Reach:</span> {tactic.expected_reach}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h3 className="font-semibold mb-3">KPI Targets</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(mktg.kpi_targets ?? []).map((kpi, i: number) => (
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
