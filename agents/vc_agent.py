"""
VC Agent — Experienced Venture Investor.

Matches the startup to 20-30 best-fit investors, builds a tailored outreach
strategy, and produces a Fundability Scorecard.

Runs last in Phase 4 (after DECKS).
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ValidationError

from agents.base_agent import BaseAgent
from schemas.vc import VCAgentOutput
from services.claude_client import ClaudeClient, make_phase4_client


class VCAgent(BaseAgent):
    """
    Experienced Venture Investor that matches the startup to real investors,
    builds an outreach strategy, and scores fundability honestly.
    """

    agent_name = "vc"
    prompt_filename = "vc_system_prompt.txt"

    def __init__(self, client: Optional[ClaudeClient] = None) -> None:
        super().__init__(client or make_phase4_client())

    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> str:
        lines = [
            "STARTUP SUBMISSION — INVESTOR MATCHING & FUNDABILITY",
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
        ]

        if upstream_context:
            # DECKS narrative — primary categorization input
            decks = upstream_context.get("decks") or {}
            if decks:
                lines += [
                    "",
                    "INVESTOR DECK NARRATIVE (from DECKS Agent — primary input for categorization)",
                    f"Narrative Arc: {decks.get('narrative_arc', 'N/A')}",
                    f"Deck Readiness Score: {decks.get('deck_readiness_score', 'N/A')}/10",
                    f"Summary: {decks.get('decks_summary', 'N/A')}",
                ]
                gaps = decks.get("data_gaps_identified", [])
                critical_gaps = [g for g in gaps if isinstance(g, dict) and g.get("severity") == "critical"]
                if critical_gaps:
                    lines.append("Critical Data Gaps (note these in fundability scorecard):")
                    for g in critical_gaps[:3]:
                        lines.append(f"  - {g.get('gap_description', '')}")

            # Financial data
            fin = upstream_context.get("phase2_fin") or {}
            if fin:
                lines += [
                    "",
                    "FINANCIAL PROFILE (from FIN Agent)",
                    f"Funding Ask: {fin.get('funding_ask', 'N/A')}",
                    f"Pre-Money Valuation: {fin.get('pre_money_valuation', 'N/A')}",
                    f"Investment Readiness Score: {fin.get('investment_readiness_score', 'N/A')}/10",
                    f"Runway: {fin.get('runway_months', 'N/A')} months",
                    f"Burn Rate: {fin.get('burn_rate_monthly', 'N/A')}/month",
                ]
                ue = fin.get("unit_economics") or {}
                if ue:
                    lines += [
                        f"LTV/CAC Ratio: {ue.get('ltv_cac_ratio', 'N/A')}",
                        f"Payback Period: {ue.get('payback_period_months', 'N/A')} months",
                        f"Gross Margin: {ue.get('gross_margin_percent', 'N/A')}",
                    ]

            # Risk
            risk = upstream_context.get("phase2_risk") or {}
            if risk:
                lines += [
                    "",
                    "RISK PROFILE (from RISK Agent)",
                    f"Overall Risk Score: {risk.get('overall_risk_score', 'N/A')}/10",
                    f"Go/No-Go: {risk.get('go_no_go_recommendation', 'N/A')}",
                    f"Critical Risks: {'; '.join(risk.get('critical_risks', [])[:3])}",
                ]

            # Phase 1 context
            phase1 = upstream_context.get("phase1_dossier") or {}
            if phase1:
                eval_r = phase1.get("eval_report") or phase1
                team_r = phase1.get("team_report") or {}
                lines += [
                    "",
                    "PHASE 1 SCORES (for fundability scoring)",
                    f"Market Viability: {eval_r.get('market_viability_score', 'N/A')}/10",
                    f"Scalability: {eval_r.get('scalability_score', 'N/A')}/10",
                    f"Founder-Market Fit: {team_r.get('founder_market_fit_score', 'N/A')}/10",
                    f"Industry: {submission_data.get('industry_vertical', 'N/A')}",
                    f"Stage: {submission_data.get('stage', 'N/A')}",
                ]
                red_flags = eval_r.get("red_flags", [])
                if red_flags:
                    lines.append(f"Phase 1 Red Flags: {'; '.join(red_flags[:3])}")

            # Customer validation
            cust = upstream_context.get("phase3_cust") or {}
            if cust:
                lines += [
                    "",
                    "CUSTOMER VALIDATION (from CUST — traction signal for fundability)",
                    f"Early Adopter Profile: {cust.get('early_adopter_profile', 'N/A')}",
                    f"Outreach Targets Identified: {len(cust.get('outreach_list', []))}",
                    f"Segments Identified: {len(cust.get('customer_segments', []))}",
                ]

        lines += [
            "",
            "IMPORTANT INSTRUCTIONS",
            "- Produce 20-30 investor entries using real, publicly known fund names.",
            "- For CleanTech/hardware/sustainability: prioritize Impact Investors with Hardware thesis.",
            "- For SaaS/EdTech: prioritize early-stage B2B SaaS funds and education-focused VCs.",
            "- If fewer than 5 genuinely matching investors exist, set mentor_consultation_required=true.",
            "- NEVER fabricate fund names.",
            "",
            "=" * 40,
            "Match investors and score fundability. Output ONLY valid JSON.",
        ]

        return "\n".join("" if item is None else str(item) for item in lines)

    def _parse_json_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        raw = super()._parse_json_response(raw)
        try:
            validated = VCAgentOutput(**raw)
            return validated.model_dump()
        except ValidationError as exc:
            raise ValueError(
                f"VC agent output failed schema validation: {exc}"
            ) from exc
