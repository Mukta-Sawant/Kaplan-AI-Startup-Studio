"""
DECKS Agent — Investor Deck Specialist.

Synthesizes all prior phase outputs into a 12-slide investor deck outline,
identifies data gaps, and scores overall deck readiness.

Runs first in Phase 4. If critical data gaps are found, the pipeline
re-runs the missing agent once before re-running DECKS.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ValidationError

from agents.base_agent import BaseAgent
from schemas.decks import DecksAgentOutput
from services.claude_client import ClaudeClient, make_phase4_client


class DecksAgent(BaseAgent):
    """
    Investor Deck Specialist that acts as Editor-in-Chief, synthesizing
    all agent outputs into a coherent 12-slide investor narrative.
    """

    agent_name = "decks"
    prompt_filename = "decks_system_prompt.txt"

    def __init__(self, client: Optional[ClaudeClient] = None) -> None:
        super().__init__(client or make_phase4_client())

    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> str:
        lines = [
            "STARTUP SUBMISSION — INVESTOR DECK SYNTHESIS",
            "=" * 40,
            f"Startup Name: {submission_data.get('startup_name', 'N/A')}",
            f"One-Line Pitch: {submission_data.get('one_line_pitch', 'N/A')}",
            f"Industry Vertical: {submission_data.get('industry_vertical', 'N/A')}",
            f"Stage: {submission_data.get('stage', 'N/A')}",
            "",
            "PROBLEM STATEMENT",
            submission_data.get("problem_statement") or "Not provided.",
            "",
            "PROPOSED SOLUTION",
            submission_data.get("proposed_solution") or "Not provided.",
            "",
            "TARGET MARKET",
            submission_data.get("target_market") or "Not provided.",
        ]

        optional_sections = [
            ("BUSINESS MODEL", "business_model"),
            ("TRACTION SUMMARY", "traction_summary"),
            ("TECHNICAL STATUS", "technical_status"),
        ]
        for heading, key in optional_sections:
            value = submission_data.get(key)
            if value:
                lines += ["", heading, str(value)]

        if upstream_context:
            # Phase 1 dossier
            phase1 = upstream_context.get("phase1_dossier") or {}
            if phase1:
                eval_r = phase1.get("eval_report") or phase1
                team_r = phase1.get("team_report") or {}
                lines += [
                    "",
                    "PHASE 1 — EVAL SCORES (for Slides 1, 3, 7, 10)",
                    f"Market Viability: {eval_r.get('market_viability_score', 'N/A')}/10",
                    f"Feasibility: {eval_r.get('feasibility_score', 'N/A')}/10",
                    f"Scalability: {eval_r.get('scalability_score', 'N/A')}/10",
                    f"Summary: {eval_r.get('summary_recommendation', 'N/A')}",
                ]
                red_flags = eval_r.get("red_flags", [])
                if red_flags:
                    lines.append(f"Red Flags: {'; '.join(red_flags[:3])}")
                lines += [
                    "",
                    "PHASE 1 — TEAM ASSESSMENT (for Slide 8)",
                    f"Founder-Market Fit Score: {team_r.get('founder_market_fit_score', 'N/A')}/10",
                    f"Identified Gaps: {', '.join(team_r.get('identified_gaps', [])[:3])}",
                    f"Recommended Mentors: {', '.join(team_r.get('recommended_mentors', [])[:3])}",
                ]
                matrix = team_r.get("role_alignment_matrix", [])
                if matrix:
                    lines.append("Team Members:")
                    for m in matrix[:5]:
                        if isinstance(m, dict):
                            lines.append(
                                f"  - {m.get('member_name', '')} ({m.get('role', '')}): "
                                f"Strengths: {', '.join(m.get('strengths', [])[:2])}"
                            )

            # Phase 2 agents
            discovery = upstream_context.get("phase2_discovery") or {}
            if discovery:
                lines += [
                    "",
                    "DISCOVERY (for Slide 3 — Market Opportunity)",
                    f"TAM: {discovery.get('total_addressable_market', 'N/A')}",
                    f"SAM: {discovery.get('serviceable_addressable_market', 'N/A')}",
                    f"SOM: {discovery.get('serviceable_obtainable_market', 'N/A')}",
                    f"Growth Rate: {discovery.get('market_growth_rate', 'N/A')}",
                    f"Trends: {'; '.join(discovery.get('key_market_trends', [])[:3])}",
                ]

            comp = upstream_context.get("phase2_comp") or {}
            if comp:
                lines += [
                    "",
                    "COMP (for Slide 7 — Competitive Landscape)",
                    f"Competitive Score: {comp.get('overall_competitive_score', 'N/A')}/10",
                    f"Moat: {comp.get('moat_assessment', 'N/A')}",
                    f"Positioning: {comp.get('competitive_positioning', 'N/A')}",
                    f"Advantages: {', '.join(comp.get('competitive_advantages', [])[:3])}",
                    f"Differentiation: {', '.join(comp.get('differentiation_factors', [])[:3])}",
                ]

            risk = upstream_context.get("phase2_risk") or {}
            if risk:
                lines += [
                    "",
                    "RISK (for Slide 10 — Risk & Mitigation)",
                    f"Overall Risk Score: {risk.get('overall_risk_score', 'N/A')}/10",
                    f"Go/No-Go: {risk.get('go_no_go_recommendation', 'N/A')}",
                    f"Critical Risks: {'; '.join(risk.get('critical_risks', [])[:3])}",
                    f"Mitigation Summary: {risk.get('risk_mitigation_summary', 'N/A')}",
                ]

            fin = upstream_context.get("phase2_fin") or {}
            if fin:
                lines += [
                    "",
                    "FINANCIALS (for Slides 9, 11 — DO NOT INFLATE)",
                    f"Funding Ask: {fin.get('funding_ask', 'N/A')}",
                    f"Pre-Money Valuation: {fin.get('pre_money_valuation', 'N/A')}",
                    f"Runway: {fin.get('runway_months', 'N/A')} months",
                    f"Investment Readiness Score: {fin.get('investment_readiness_score', 'N/A')}/10",
                    f"Break-Even: {fin.get('break_even_timeline', 'N/A')}",
                ]
                projections = fin.get("revenue_projections", [])
                if projections:
                    lines.append("Revenue Projections (use exact figures):")
                    for p in projections:
                        if isinstance(p, dict):
                            lines.append(
                                f"  Year {p.get('year', '')}: Revenue {p.get('revenue', '')}, "
                                f"EBITDA {p.get('ebitda', '')}"
                            )
                ue = fin.get("unit_economics") or {}
                if ue:
                    lines += [
                        f"CAC: {ue.get('customer_acquisition_cost', 'N/A')}",
                        f"LTV: {ue.get('lifetime_value', 'N/A')}",
                        f"LTV/CAC: {ue.get('ltv_cac_ratio', 'N/A')}",
                    ]
                use_of_funds = fin.get("use_of_funds", [])
                if use_of_funds:
                    lines.append(f"Use of Funds: {', '.join(use_of_funds[:4])}")

            interact = upstream_context.get("phase2_interact") or {}
            if interact:
                gaps = interact.get("information_gaps", [])
                if gaps:
                    lines += [
                        "",
                        "INFORMATION GAPS (from INTERACT — flag these as data gaps in deck)",
                        *[f"  - {g}" for g in gaps[:3]],
                    ]

            gtm = upstream_context.get("phase2_gtm") or {}
            if gtm:
                lines += [
                    "",
                    "GTM (for Slide 6)",
                    f"Value Proposition: {gtm.get('value_proposition', 'N/A')}",
                    f"Pricing Model: {gtm.get('pricing_model', 'N/A')}",
                    f"Primary Segments: {', '.join(gtm.get('primary_target_segments', []))}",
                    f"Launch Timeline: {gtm.get('launch_timeline', 'N/A')}",
                ]

            # Phase 3 agents
            cust = upstream_context.get("phase3_cust") or {}
            if cust:
                lines += [
                    "",
                    "CUSTOMER VALIDATION (from CUST — for Slide 4 Traction)",
                    f"Early Adopter Profile: {cust.get('early_adopter_profile', 'N/A')}",
                ]
                outreach = cust.get("outreach_list", [])
                if outreach:
                    lines.append(f"Outreach Targets Identified: {len(outreach)}")

            channels = upstream_context.get("phase3_channels") or {}
            if channels:
                top = channels.get("outreach_priority_ranking", [])
                if top:
                    lines += [
                        "",
                        "PARTNERSHIPS (from CHANNELS — for Slide 6)",
                        f"Top Partners: {', '.join(top[:5])}",
                    ]

            mktg = upstream_context.get("phase3_mktg") or {}
            if mktg:
                kpis = mktg.get("kpi_targets", [])
                if kpis:
                    lines += [
                        "",
                        "MARKETING KPIs (from MKTG — for Slide 6)",
                        *[
                            f"  - {k.get('metric', '')}: {k.get('target_value', '')}"
                            for k in kpis[:3] if isinstance(k, dict)
                        ],
                    ]

        lines += [
            "",
            "=" * 40,
            "Produce a 12-slide investor deck outline. Identify all data gaps. Output ONLY valid JSON.",
        ]

        return "\n".join("" if item is None else str(item) for item in lines)

    def _parse_json_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        raw = super()._parse_json_response(raw)
        try:
            validated = DecksAgentOutput(**raw)
            return validated.model_dump()
        except ValidationError as exc:
            raise ValueError(
                f"DECKS agent output failed schema validation: {exc}"
            ) from exc
