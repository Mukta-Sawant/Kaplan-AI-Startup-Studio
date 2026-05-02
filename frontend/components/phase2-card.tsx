"use client";

import { useState } from "react";

import type {
  CompReport,
  DiscoveryReport,
  FinReport,
  GTMReport,
  InteractReport,
  Phase2Output,
  RiskReport,
} from "@/lib/types";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function ConfidencePill({ value }: { value: number | null | undefined }) {
  if (value == null) return null;
  const pct = Math.round(value * 100);
  const color =
    pct >= 70 ? "bg-green-100 text-green-700" :
    pct >= 45 ? "bg-amber-100 text-amber-700" :
    "bg-red-100 text-red-700";
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${color}`}>
      {pct}% confidence
    </span>
  );
}

function ScoreBadge({ label, value, max = 10, colorFn }: {
  label: string;
  value: number | null | undefined;
  max?: number;
  colorFn?: (v: number) => string;
}) {
  if (value == null) return null;
  const defaultColor = value >= max * 0.7 ? "bg-green-100 text-green-800" :
    value >= max * 0.4 ? "bg-amber-100 text-amber-800" :
    "bg-red-100 text-red-800";
  return (
    <div className={`rounded-xl px-4 py-3 text-center ${colorFn ? colorFn(value) : defaultColor}`}>
      <p className="text-2xl font-bold">{value}<span className="text-sm font-normal">/{max}</span></p>
      <p className="text-xs mt-0.5">{label}</p>
    </div>
  );
}

function SectionCard({ title, status, children }: {
  title: string;
  status?: "success" | "failed";
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">{title}</h2>
        {status === "failed" && (
          <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Agent Failed</span>
        )}
      </div>
      {children}
    </div>
  );
}

function BulletList({ items, color = "text-gray-700" }: { items: string[]; color?: string }) {
  if (!items?.length) return <p className="text-sm text-gray-400 italic">None identified.</p>;
  return (
    <ul className="space-y-1">
      {items.map((item, i) => (
        <li key={i} className={`text-sm flex items-start gap-2 ${color}`}>
          <span className="mt-0.5 shrink-0">•</span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

// ---------------------------------------------------------------------------
// INTERACT section
// ---------------------------------------------------------------------------

function InteractSection({ data, status }: { data: InteractReport | null; status: string }) {
  return (
    <SectionCard title="INTERACT — Clarification Questions" status={status as "success" | "failed"}>
      {!data ? <p className="text-sm text-gray-400">No data available.</p> : (
        <>
          <div className="flex items-center gap-3 mb-4">
            <span className="text-sm text-gray-500">{data.clarification_questions?.length ?? 0} questions generated</span>
            <ConfidencePill value={data.confidence_level} />
          </div>

          {data.priority_topics?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Priority Topics</p>
              <div className="flex flex-wrap gap-2">
                {data.priority_topics.map((t, i) => (
                  <span key={i} className="bg-brand-50 text-brand-700 border border-brand-100 text-xs px-3 py-1 rounded-full">{t}</span>
                ))}
              </div>
            </div>
          )}

          {data.clarification_questions?.length > 0 && (
            <div className="space-y-3">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Questions (ranked by priority)</p>
              {[...data.clarification_questions]
                .sort((a, b) => a.priority - b.priority)
                .map((q, i) => (
                  <div key={i} className="border border-gray-100 rounded-xl p-4 bg-gray-50">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-medium text-gray-800">{q.question}</p>
                      <span className="shrink-0 text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">P{q.priority}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{q.rationale}</p>
                    <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full mt-2 inline-block capitalize">
                      {q.topic_area?.replace(/_/g, " ")}
                    </span>
                  </div>
                ))}
            </div>
          )}

          {data.information_gaps?.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Information Gaps</p>
              <BulletList items={data.information_gaps} color="text-orange-700" />
            </div>
          )}

          <p className="mt-4 text-sm text-gray-700 italic border-l-2 border-brand-300 pl-3">
            {data.interaction_summary}
          </p>
        </>
      )}
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// DISCOVERY section
// ---------------------------------------------------------------------------

function DiscoverySection({ data, status }: { data: DiscoveryReport | null; status: string }) {
  return (
    <SectionCard title="DISCOVERY — Market Analysis" status={status as "success" | "failed"}>
      {!data ? <p className="text-sm text-gray-400">No data available.</p> : (
        <>
          <div className="flex items-center gap-3 mb-4">
            <span className={`text-xs px-2 py-0.5 rounded-full capitalize font-medium ${
              data.industry_maturity === "growth" ? "bg-green-100 text-green-700" :
              data.industry_maturity === "emerging" ? "bg-blue-100 text-blue-700" :
              data.industry_maturity === "mature" ? "bg-gray-100 text-gray-700" :
              "bg-amber-100 text-amber-700"
            }`}>{data.industry_maturity}</span>
            <ConfidencePill value={data.confidence_level} />
          </div>

          <div className="grid grid-cols-3 gap-3 mb-5">
            {[
              { label: "TAM", value: data.total_addressable_market },
              { label: "SAM", value: data.serviceable_addressable_market },
              { label: "SOM", value: data.serviceable_obtainable_market },
            ].map(({ label, value }) => (
              <div key={label} className="bg-blue-50 rounded-xl p-3 text-center">
                <p className="text-xs text-blue-500 font-medium">{label}</p>
                <p className="text-sm font-semibold text-blue-900 mt-0.5 leading-tight">{value || "—"}</p>
              </div>
            ))}
          </div>

          <div className="mb-4">
            <p className="text-xs font-medium text-gray-500 mb-1">Growth Rate</p>
            <p className="text-sm text-gray-800">{data.market_growth_rate || "—"}</p>
          </div>

          {data.key_market_trends?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Key Trends</p>
              <BulletList items={data.key_market_trends} />
            </div>
          )}

          {data.market_opportunities?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Opportunities</p>
              <BulletList items={data.market_opportunities} color="text-green-700" />
            </div>
          )}

          {data.market_threats?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Threats</p>
              <BulletList items={data.market_threats} color="text-red-700" />
            </div>
          )}

          {data.market_entry_barriers?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Entry Barriers</p>
              <BulletList items={data.market_entry_barriers} color="text-orange-700" />
            </div>
          )}

          <div className="mb-4">
            <p className="text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Regulatory Landscape</p>
            <p className="text-sm text-gray-700 leading-relaxed">{data.regulatory_landscape}</p>
          </div>

          <p className="mt-4 text-sm text-gray-700 italic border-l-2 border-blue-300 pl-3">
            {data.discovery_summary}
          </p>
        </>
      )}
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// COMP section
// ---------------------------------------------------------------------------

function CompSection({ data, status }: { data: CompReport | null; status: string }) {
  return (
    <SectionCard title="COMP — Competitive Analysis" status={status as "success" | "failed"}>
      {!data ? <p className="text-sm text-gray-400">No data available.</p> : (
        <>
          <div className="flex items-center gap-4 mb-5">
            <ScoreBadge label="Competitive Score" value={data.overall_competitive_score} />
            <ConfidencePill value={data.confidence_level} />
          </div>

          <div className="mb-4">
            <p className="text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Positioning</p>
            <p className="text-sm text-gray-800">{data.competitive_positioning}</p>
          </div>

          <div className="mb-4">
            <p className="text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Moat Assessment</p>
            <p className="text-sm text-gray-700 leading-relaxed">{data.moat_assessment}</p>
          </div>

          {data.direct_competitors?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">
                Direct Competitors ({data.direct_competitors.length})
              </p>
              <div className="space-y-3">
                {data.direct_competitors.map((c, i) => (
                  <div key={i} className="border border-red-100 rounded-xl p-3 bg-red-50">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium">{c.name}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        c.threat_level === "high" ? "bg-red-200 text-red-800" :
                        c.threat_level === "medium" ? "bg-amber-100 text-amber-700" :
                        "bg-green-100 text-green-700"
                      }`}>{c.threat_level} threat</span>
                    </div>
                    {c.strengths?.length > 0 && (
                      <p className="text-xs text-gray-600 mt-1"><span className="font-medium">Strengths: </span>{c.strengths.join(", ")}</p>
                    )}
                    {c.weaknesses?.length > 0 && (
                      <p className="text-xs text-gray-600 mt-0.5"><span className="font-medium">Weaknesses: </span>{c.weaknesses.join(", ")}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {data.competitive_advantages?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Our Advantages</p>
              <BulletList items={data.competitive_advantages} color="text-green-700" />
            </div>
          )}

          {data.white_space_opportunities?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">White Space Opportunities</p>
              <BulletList items={data.white_space_opportunities} color="text-blue-700" />
            </div>
          )}

          <p className="mt-4 text-sm text-gray-700 italic border-l-2 border-purple-300 pl-3">
            {data.comp_summary}
          </p>
        </>
      )}
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// RISK section
// ---------------------------------------------------------------------------

const RISK_LEVEL_STYLE: Record<string, string> = {
  low: "bg-green-100 text-green-700",
  medium: "bg-amber-100 text-amber-700",
  high: "bg-red-100 text-red-700",
};

function RiskSection({ data, status }: { data: RiskReport | null; status: string }) {
  return (
    <SectionCard title="RISK — Risk Register" status={status as "success" | "failed"}>
      {!data ? <p className="text-sm text-gray-400">No data available.</p> : (
        <>
          <div className="flex items-center gap-4 mb-5">
            <ScoreBadge
              label="Overall Risk"
              value={data.overall_risk_score}
              colorFn={(v) => v <= 3 ? "bg-green-100 text-green-800" : v <= 6 ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800"}
            />
            <div>
              <p className="text-xs text-gray-500">Recommendation</p>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                data.go_no_go_recommendation === "conditional_go" ? "bg-green-100 text-green-700" :
                data.go_no_go_recommendation === "proceed_with_caution" ? "bg-amber-100 text-amber-700" :
                data.go_no_go_recommendation === "high_risk_proceed" ? "bg-orange-100 text-orange-700" :
                "bg-red-100 text-red-700"
              }`}>
                {data.go_no_go_recommendation?.replace(/_/g, " ")}
              </span>
            </div>
            <ConfidencePill value={data.confidence_level} />
          </div>

          {data.critical_risks?.length > 0 && (
            <div className="mb-4 p-3 bg-red-50 border border-red-100 rounded-xl">
              <p className="text-xs font-medium text-red-700 mb-2 uppercase tracking-wide">Critical Risks</p>
              <BulletList items={data.critical_risks} color="text-red-700" />
            </div>
          )}

          {data.risk_register?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">
                Risk Register ({data.risk_register.length} risks)
              </p>
              <div className="space-y-2">
                {data.risk_register.map((r, i) => (
                  <div key={i} className="border border-gray-100 rounded-xl p-3 bg-gray-50">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-mono text-gray-400">{r.risk_id}</span>
                          <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full capitalize">{r.category}</span>
                        </div>
                        <p className="text-sm text-gray-800">{r.description}</p>
                        <p className="text-xs text-gray-500 mt-1"><span className="font-medium">Mitigation: </span>{r.mitigation_strategy}</p>
                      </div>
                      <div className="flex flex-col gap-1 shrink-0 items-end">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${RISK_LEVEL_STYLE[r.probability] ?? "bg-gray-100 text-gray-600"}`}>
                          P: {r.probability}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${RISK_LEVEL_STYLE[r.impact] ?? "bg-gray-100 text-gray-600"}`}>
                          I: {r.impact}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="mt-4 text-sm text-gray-700 italic border-l-2 border-red-300 pl-3">
            {data.risk_mitigation_summary}
          </p>
        </>
      )}
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// GTM section
// ---------------------------------------------------------------------------

function GTMSection({ data, status }: { data: GTMReport | null; status: string }) {
  return (
    <SectionCard title="GTM — Go-To-Market Strategy" status={status as "success" | "failed"}>
      {!data ? <p className="text-sm text-gray-400">No data available.</p> : (
        <>
          <div className="flex items-center gap-3 mb-4">
            <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium capitalize">
              {data.pricing_model?.replace(/-/g, " ")}
            </span>
            <ConfidencePill value={data.confidence_level} />
          </div>

          <div className="mb-4">
            <p className="text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Value Proposition</p>
            <p className="text-sm text-gray-800 leading-relaxed">{data.value_proposition}</p>
          </div>

          <div className="mb-4">
            <p className="text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Ideal Customer Profile</p>
            <p className="text-sm text-gray-700 leading-relaxed">{data.ideal_customer_profile}</p>
          </div>

          {data.primary_target_segments?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Target Segments</p>
              <div className="flex flex-wrap gap-2">
                {data.primary_target_segments.map((s, i) => (
                  <span key={i} className="bg-indigo-50 text-indigo-700 border border-indigo-100 text-xs px-3 py-1 rounded-full">{s}</span>
                ))}
              </div>
            </div>
          )}

          <div className="mb-4">
            <p className="text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Pricing Strategy</p>
            <p className="text-sm text-gray-700 leading-relaxed">{data.pricing_strategy}</p>
          </div>

          {data.marketing_channels?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Channels</p>
              <div className="space-y-2">
                {[...data.marketing_channels]
                  .sort((a, b) => a.priority - b.priority)
                  .map((ch, i) => (
                    <div key={i} className="border border-indigo-100 rounded-xl p-3 bg-indigo-50">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">{ch.channel}</p>
                        <span className="text-xs bg-white text-indigo-600 border border-indigo-200 px-2 py-0.5 rounded-full">P{ch.priority}</span>
                      </div>
                      <p className="text-xs text-gray-600 mt-1">{ch.strategy}</p>
                      <div className="flex gap-3 mt-1 text-xs text-gray-500">
                        <span>Cost: {ch.estimated_cost}</span>
                        <span>Reach: {ch.expected_reach}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          <div className="mb-4">
            <p className="text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Launch Timeline</p>
            <p className="text-sm text-gray-700 leading-relaxed">{data.launch_timeline}</p>
          </div>

          {data.key_partnerships?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Key Partnerships</p>
              <BulletList items={data.key_partnerships} />
            </div>
          )}

          {data.success_metrics?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Success Metrics</p>
              <BulletList items={data.success_metrics} color="text-green-700" />
            </div>
          )}

          <p className="mt-4 text-sm text-gray-700 italic border-l-2 border-indigo-300 pl-3">
            {data.gtm_summary}
          </p>
        </>
      )}
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// FIN section
// ---------------------------------------------------------------------------

function FinSection({ data, status }: { data: FinReport | null; status: string }) {
  return (
    <SectionCard title="FIN — Financial Analysis" status={status as "success" | "failed"}>
      {!data ? <p className="text-sm text-gray-400">No data available.</p> : (
        <>
          <div className="flex items-center gap-4 mb-5">
            <ScoreBadge label="Investment Readiness" value={data.investment_readiness_score} />
            <div className="space-y-1">
              <div>
                <p className="text-xs text-gray-500">Funding Ask</p>
                <p className="text-sm font-semibold text-gray-800">{data.funding_ask || "—"}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Runway</p>
                <p className="text-sm font-semibold text-gray-800">{data.runway_months} months</p>
              </div>
            </div>
            <ConfidencePill value={data.confidence_level} />
          </div>

          {data.revenue_projections?.length > 0 && (
            <div className="mb-5">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">3-Year Projections</p>
              <div className="grid grid-cols-3 gap-3">
                {data.revenue_projections.map((p, i) => (
                  <div key={i} className="bg-emerald-50 border border-emerald-100 rounded-xl p-3">
                    <p className="text-xs font-medium text-emerald-600 mb-1">Year {p.year}</p>
                    <p className="text-sm font-bold text-emerald-900">{p.revenue}</p>
                    <p className="text-xs text-emerald-700 mt-0.5">GM: {p.gross_margin}</p>
                    <p className="text-xs text-emerald-700">EBITDA: {p.ebitda}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{p.headcount} headcount</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {data.unit_economics && (
            <div className="mb-5">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Unit Economics</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {[
                  { label: "CAC", value: data.unit_economics.customer_acquisition_cost },
                  { label: "LTV", value: data.unit_economics.lifetime_value },
                  { label: "LTV:CAC", value: data.unit_economics.ltv_cac_ratio },
                  { label: "Payback", value: `${data.unit_economics.payback_period_months}mo` },
                  { label: "Gross Margin", value: data.unit_economics.gross_margin_percent },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-gray-50 border border-gray-100 rounded-xl p-3 text-center">
                    <p className="text-xs text-gray-500">{label}</p>
                    <p className="text-sm font-semibold text-gray-800 mt-0.5">{value || "—"}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mb-4 grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1">Burn Rate (Monthly)</p>
              <p className="text-sm text-gray-800">{data.burn_rate_monthly || "—"}</p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1">Pre-Money Valuation</p>
              <p className="text-sm text-gray-800">{data.pre_money_valuation || "—"}</p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1">Break-Even Timeline</p>
              <p className="text-sm text-gray-800">{data.break_even_timeline || "—"}</p>
            </div>
          </div>

          {data.use_of_funds?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Use of Funds</p>
              <BulletList items={data.use_of_funds} />
            </div>
          )}

          {data.key_financial_assumptions?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Key Assumptions</p>
              <BulletList items={data.key_financial_assumptions} color="text-blue-700" />
            </div>
          )}

          {data.financial_risk_factors?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Financial Risk Factors</p>
              <BulletList items={data.financial_risk_factors} color="text-red-700" />
            </div>
          )}

          <p className="mt-4 text-sm text-gray-700 italic border-l-2 border-emerald-300 pl-3">
            {data.fin_summary}
          </p>
        </>
      )}
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// Main Phase2Card
// ---------------------------------------------------------------------------

interface Phase2CardProps {
  output: Phase2Output;
}

type AgentKey = "interact" | "discovery" | "comp" | "risk" | "gtm" | "fin";

export function Phase2Card({ output }: Phase2CardProps) {
  const statuses = output.agent_statuses ?? {};
  const [selectedAgent, setSelectedAgent] = useState<AgentKey>("interact");

  const agentSections = [
    {
      key: "interact" as const,
      label: "INTERACT",
      title: "Clarification Questions",
      status: statuses.interact,
      summary: output.interact?.interaction_summary ?? "Clarification questions and information gaps.",
      render: () => <InteractSection data={output.interact} status={statuses.interact} />,
    },
    {
      key: "discovery" as const,
      label: "DISCOVERY",
      title: "Market Analysis",
      status: statuses.discovery,
      summary: output.discovery?.discovery_summary ?? "Market size, barriers, and growth signals.",
      render: () => <DiscoverySection data={output.discovery} status={statuses.discovery} />,
    },
    {
      key: "comp" as const,
      label: "COMP",
      title: "Competitive Analysis",
      status: statuses.comp,
      summary: output.comp?.comp_summary ?? "Competitive positioning and moat assessment.",
      render: () => <CompSection data={output.comp} status={statuses.comp} />,
    },
    {
      key: "risk" as const,
      label: "RISK",
      title: "Risk Register",
      status: statuses.risk,
      summary: output.risk?.risk_mitigation_summary ?? "Critical risks and mitigation strategy.",
      render: () => <RiskSection data={output.risk} status={statuses.risk} />,
    },
    {
      key: "gtm" as const,
      label: "GTM",
      title: "Go-To-Market Strategy",
      status: statuses.gtm,
      summary: output.gtm?.gtm_summary ?? "Target segments, channels, and launch plan.",
      render: () => <GTMSection data={output.gtm} status={statuses.gtm} />,
    },
    {
      key: "fin" as const,
      label: "FIN",
      title: "Financial Analysis",
      status: statuses.fin,
      summary: output.fin?.fin_summary ?? "Funding, runway, and unit economics.",
      render: () => <FinSection data={output.fin} status={statuses.fin} />,
    },
  ];

  const activeAgent =
    agentSections.find((section) => section.key === selectedAgent) ?? agentSections[0];

  return (
    <div className="space-y-8">
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-gray-500">
              Phase 2 Agent Viewer
            </p>
            <h2 className="mt-2 text-xl font-semibold text-slate-900">
              {activeAgent.label} <span className="text-gray-400">|</span> {activeAgent.title}
            </h2>
            <p className="mt-1 max-w-2xl text-sm text-gray-600">
              {activeAgent.summary}
            </p>
          </div>
          <div className="w-full max-w-sm">
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Select Agent
            </label>
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value as AgentKey)}
              className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {agentSections.map((section) => (
                <option key={section.key} value={section.key}>
                  {section.label} - {section.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-2 md:grid-cols-3 xl:grid-cols-6">
          {agentSections.map((section) => {
            const isActive = section.key === activeAgent.key;
            const statusClass =
              section.status === "success"
                ? "border-green-200 bg-green-50 text-green-700"
                : "border-red-200 bg-red-50 text-red-700";
            return (
              <button
                key={section.key}
                type="button"
                onClick={() => setSelectedAgent(section.key)}
                className={`rounded-xl border px-3 py-3 text-left transition-all ${
                  isActive
                    ? "border-brand-500 bg-brand-500 text-white shadow-sm"
                    : statusClass
                }`}
              >
                <p className="text-sm font-semibold">{section.label}</p>
                <p className={`text-xs ${isActive ? "text-white/80" : ""}`}>
                  {section.status ?? "unknown"}
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
