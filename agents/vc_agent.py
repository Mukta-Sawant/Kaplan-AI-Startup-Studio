"""
VC Agent - Experienced Venture Investor.

Matches the startup to 20 best-fit investors, builds a tailored outreach
strategy, and produces a Fundability Scorecard.

Runs last in Phase 4 (after DECKS).
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ValidationError

from agents.base_agent import BaseAgent
from schemas.vc import VCAgentOutput
from services.claude_client import ClaudeClient, make_vc_client


class VCAgent(BaseAgent):
    """
    Experienced Venture Investor that matches the startup to real investors,
    builds an outreach strategy, and scores fundability honestly.
    """

    agent_name = "vc"
    prompt_filename = "vc_system_prompt.txt"

    def __init__(self, client: Optional[ClaudeClient] = None) -> None:
        super().__init__(client or make_vc_client())

    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> str:
        def trim(val: Any, n: int = 180) -> str:
            s = str(val or "N/A").strip()
            return s[:n] + "..." if len(s) > n else s

        lines = [
            "STARTUP - INVESTOR MATCHING AND FUNDABILITY",
            f"Name: {submission_data.get('startup_name', 'N/A')} | Industry: {submission_data.get('industry_vertical', 'N/A')} | Stage: {submission_data.get('stage', 'N/A')}",
            f"Pitch: {trim(submission_data.get('one_line_pitch'), 110)}",
            f"Problem: {trim(submission_data.get('problem_statement'), 150)}",
            f"Solution: {trim(submission_data.get('proposed_solution'), 150)}",
        ]

        if upstream_context:
            decks = upstream_context.get("decks") or {}
            if decks:
                gaps = decks.get("data_gaps_identified") or []
                critical_gaps = [
                    gap
                    for gap in gaps
                    if isinstance(gap, dict) and gap.get("severity") == "critical"
                ]
                lines += [
                    "",
                    "DECKS NARRATIVE",
                    f"Narrative Arc: {trim(decks.get('narrative_arc'), 180)}",
                    f"Deck Readiness: {decks.get('deck_readiness_score', 'N/A')}/10",
                    f"Deck Summary: {trim(decks.get('decks_summary'), 140)}",
                ]
                if critical_gaps:
                    lines.append(
                        "Critical Gaps: "
                        + "; ".join(
                            trim(gap.get("gap_description", ""), 70)
                            for gap in critical_gaps[:2]
                        )
                    )

            fin = upstream_context.get("phase2_fin") or {}
            if fin:
                lines += [
                    "",
                    "FINANCIAL PROFILE",
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

            risk = upstream_context.get("phase2_risk") or {}
            if risk:
                lines += [
                    "",
                    "RISK PROFILE",
                    f"Overall Risk Score: {risk.get('overall_risk_score', 'N/A')}/10",
                    f"Recommendation: {trim(risk.get('go_no_go_recommendation'), 80)}",
                    f"Critical Risks: {'; '.join((risk.get('critical_risks') or [])[:3])}",
                ]

            phase1 = upstream_context.get("phase1_dossier") or {}
            if phase1:
                eval_r = phase1.get("eval_report") or phase1
                team_r = phase1.get("team_report") or {}
                red_flags = (eval_r.get("red_flags") or [])[:3]
                lines += [
                    "",
                    "PHASE 1 SCORES",
                    f"Market: {eval_r.get('market_viability_score', 'N/A')}/10",
                    f"Scalability: {eval_r.get('scalability_score', 'N/A')}/10",
                    f"Founder-Market Fit: {team_r.get('founder_market_fit_score', 'N/A')}/10",
                ]
                if red_flags:
                    lines.append(f"Red Flags: {'; '.join(red_flags)}")

            cust = upstream_context.get("phase3_cust") or {}
            if cust:
                lines += [
                    "",
                    "CUSTOMER VALIDATION",
                    f"Early Adopter: {trim(cust.get('early_adopter_profile'), 120)}",
                    f"Customer Segments: {len(cust.get('customer_segments') or [])}",
                    f"Outreach Targets: {len(cust.get('outreach_list') or [])}",
                ]

        lines += [
            "",
            "IMPORTANT INSTRUCTIONS",
            "- Produce exactly 20 investor entries using real, publicly known fund names.",
            "- Keep every string short and factual.",
            "- Do not use markdown or code fences.",
            "- thesis_fit must be one short sentence.",
            "- portfolio_examples must contain only 1 or 2 company names.",
            "- warm_intro_path must be very short.",
            "- outreach_strategy lists must stay short.",
            "- fundability score explanations must be short phrases, not paragraphs.",
            "- vc_summary must be exactly 2 short sentences.",
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
