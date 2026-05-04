"""
DECKS Agent - Investor Deck Specialist.

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
from services.claude_client import ClaudeClient, make_decks_client


class DecksAgent(BaseAgent):
    """
    Investor Deck Specialist that acts as Editor-in-Chief, synthesizing
    all agent outputs into a coherent 12-slide investor narrative.
    """

    agent_name = "decks"
    prompt_filename = "decks_system_prompt.txt"

    def __init__(self, client: Optional[ClaudeClient] = None) -> None:
        super().__init__(client or make_decks_client())

    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> str:
        def trim(val: Any, n: int = 140) -> str:
            s = str(val or "N/A").strip()
            return s[:n] + "..." if len(s) > n else s

        def bullet(items: Any, n: int = 2, item_chars: int = 60) -> str:
            values = items if isinstance(items, list) else []
            return "; ".join(trim(item, item_chars) for item in values[:n]) or "N/A"

        lines = [
            "STARTUP - INVESTOR DECK SYNTHESIS",
            f"Name: {submission_data.get('startup_name', 'N/A')}",
            f"Industry: {submission_data.get('industry_vertical', 'N/A')}",
            f"Stage: {submission_data.get('stage', 'N/A')}",
            f"Pitch: {trim(submission_data.get('one_line_pitch'), 100)}",
            f"Problem: {trim(submission_data.get('problem_statement'), 140)}",
            f"Solution: {trim(submission_data.get('proposed_solution'), 140)}",
            f"Market: {trim(submission_data.get('target_market'), 110)}",
        ]

        for label, key in [
            ("Model", "business_model"),
            ("Traction", "traction_summary"),
            ("Tech", "technical_status"),
        ]:
            value = submission_data.get(key)
            if value:
                lines.append(f"{label}: {trim(value, 110)}")

        if upstream_context:
            phase1 = upstream_context.get("phase1_dossier") or {}
            if phase1:
                eval_report = phase1.get("eval_report") or phase1
                team_report = phase1.get("team_report") or {}
                lines += [
                    "",
                    "PHASE 1",
                    f"EVAL Scores: Market {eval_report.get('market_viability_score', 'N/A')}/10 | Feasibility {eval_report.get('feasibility_score', 'N/A')}/10 | Scalability {eval_report.get('scalability_score', 'N/A')}/10",
                    f"EVAL Summary: {trim(eval_report.get('summary_recommendation'), 120)}",
                    f"EVAL Red Flags: {bullet(eval_report.get('red_flags'), 2)}",
                    f"TEAM Founder-Market Fit: {team_report.get('founder_market_fit_score', 'N/A')}/10",
                    f"TEAM Gaps: {bullet(team_report.get('identified_gaps'), 2)}",
                    f"TEAM Mentor Needs: {bullet(team_report.get('recommended_mentors'), 2)}",
                ]

            discovery = upstream_context.get("phase2_discovery") or {}
            if discovery:
                lines += [
                    "",
                    "DISCOVERY",
                    f"TAM: {discovery.get('total_addressable_market', 'N/A')}",
                    f"SAM: {discovery.get('serviceable_addressable_market', 'N/A')}",
                    f"SOM: {discovery.get('serviceable_obtainable_market', 'N/A')}",
                    f"Growth: {discovery.get('market_growth_rate', 'N/A')}",
                    f"Trends: {bullet(discovery.get('key_market_trends'), 2)}",
                    f"Barriers: {bullet(discovery.get('market_entry_barriers'), 2)}",
                ]

            comp = upstream_context.get("phase2_comp") or {}
            if comp:
                direct_names = [
                    entry.get("name", "")
                    for entry in (comp.get("direct_competitors") or [])[:3]
                    if isinstance(entry, dict)
                ]
                lines += [
                    "",
                    "COMP",
                    f"Competitive Score: {comp.get('overall_competitive_score', 'N/A')}/10",
                    f"Direct Competitors: {', '.join(filter(None, direct_names)) or 'N/A'}",
                    f"Moat: {trim(comp.get('moat_assessment'), 100)}",
                    f"Positioning: {trim(comp.get('competitive_positioning'), 100)}",
                    f"Advantages: {bullet(comp.get('competitive_advantages'), 2)}",
                ]

            risk = upstream_context.get("phase2_risk") or {}
            if risk:
                lines += [
                    "",
                    "RISK",
                    f"Risk Score: {risk.get('overall_risk_score', 'N/A')}/10",
                    f"Recommendation: {trim(risk.get('go_no_go_recommendation'), 80)}",
                    f"Critical Risks: {bullet(risk.get('critical_risks'), 2)}",
                    f"Mitigation: {trim(risk.get('risk_mitigation_summary'), 100)}",
                ]

            gtm = upstream_context.get("phase2_gtm") or {}
            if gtm:
                lines += [
                    "",
                    "GTM",
                    f"Primary Segments: {bullet(gtm.get('primary_target_segments'), 2)}",
                    f"Value Proposition: {trim(gtm.get('value_proposition'), 100)}",
                    f"Pricing Model: {gtm.get('pricing_model', 'N/A')}",
                    f"Acquisition: {trim(gtm.get('customer_acquisition_strategy'), 90)}",
                    f"Metrics: {bullet(gtm.get('success_metrics'), 2)}",
                ]

            fin = upstream_context.get("phase2_fin") or {}
            if fin:
                unit_economics = fin.get("unit_economics") or {}
                lines += [
                    "",
                    "FIN",
                    f"Funding Ask: {fin.get('funding_ask', 'N/A')}",
                    f"Valuation: {fin.get('pre_money_valuation', 'N/A')}",
                    f"Runway: {fin.get('runway_months', 'N/A')} months",
                    f"Burn Rate: {fin.get('burn_rate_monthly', 'N/A')}/month",
                    f"Readiness: {fin.get('investment_readiness_score', 'N/A')}/10",
                    f"LTV/CAC: {unit_economics.get('ltv_cac_ratio', 'N/A')}",
                    f"Gross Margin: {unit_economics.get('gross_margin_percent', 'N/A')}",
                    f"Use of Funds: {bullet(fin.get('use_of_funds'), 2)}",
                ]

            interact = upstream_context.get("phase2_interact") or {}
            if interact:
                lines += [
                    "",
                    "INTERACT",
                    f"Information Gaps: {bullet(interact.get('information_gaps'), 2)}",
                    f"Priority Topics: {bullet(interact.get('priority_topics'), 2)}",
                ]

            cust = upstream_context.get("phase3_cust") or {}
            if cust:
                lines += [
                    "",
                    "CUSTOMER VALIDATION",
                    f"Early Adopter: {trim(cust.get('early_adopter_profile'), 100)}",
                    f"Customer Segments: {len(cust.get('customer_segments') or [])}",
                    f"Outreach Targets: {len(cust.get('outreach_list') or [])}",
                    f"Summary: {trim(cust.get('cust_summary'), 90)}",
                ]

            channels = upstream_context.get("phase3_channels") or {}
            if channels:
                lines += [
                    "",
                    "CHANNELS",
                    f"Top Partners: {bullet(channels.get('outreach_priority_ranking'), 3)}",
                    f"Partnership Gaps: {bullet(channels.get('partnership_gaps'), 2)}",
                    f"Summary: {trim(channels.get('channels_summary'), 90)}",
                ]

            mktg = upstream_context.get("phase3_mktg") or {}
            if mktg:
                lines += [
                    "",
                    "MKTG",
                    f"Summary: {trim(mktg.get('mktg_summary'), 90)}",
                ]

        lines += [
            "",
            "IMPORTANT INSTRUCTIONS",
            "- Produce exactly 12 slides in the required order.",
            "- Keep titles short.",
            "- Use exactly 3 short key points per slide.",
            "- Use exactly 2 short sentences for speaker notes.",
            "- Keep narrative_arc to 2 short sentences.",
            "- Keep decks_summary to 3 short sentences.",
            "- Include only the most important data gaps.",
            "- Do not use markdown or code fences.",
            "- Output ONLY valid JSON.",
        ]

        return "\n".join(str(item) for item in lines)

    def _parse_json_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        raw = super()._parse_json_response(raw)
        try:
            validated = DecksAgentOutput(**raw)
            return validated.model_dump()
        except ValidationError as exc:
            raise ValueError(
                f"DECKS agent output failed schema validation: {exc}"
            ) from exc
