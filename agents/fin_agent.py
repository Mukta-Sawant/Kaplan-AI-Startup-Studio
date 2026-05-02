"""
FIN Agent — Early-Stage CFO.

Builds 3-year revenue projections, assesses burn/runway, evaluates unit
economics, sizes the funding ask, and identifies key financial risks.

IMPORTANT: FIN runs AFTER GTM in the Phase 2 pipeline, receiving GTM
output as upstream context so projections are consistent with the
recommended pricing model and channel strategy.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ValidationError

from agents.base_agent import BaseAgent
from schemas.fin import FinAgentOutput
from services.claude_client import ClaudeClient, make_phase2_client


class FinAgent(BaseAgent):
    """
    Early-Stage CFO that builds financial models grounded in the GTM
    strategy, market data, and Phase 1 dossier context.
    Sequenced after GTM to ensure model consistency.
    """

    agent_name = "fin"
    prompt_filename = "fin_system_prompt.txt"

    def __init__(self, client: Optional[ClaudeClient] = None) -> None:
        super().__init__(client or make_phase2_client())

    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> str:
        lines = [
            "STARTUP SUBMISSION — FINANCIAL ANALYSIS",
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
            # GTM context — critical for financial modeling
            gtm = upstream_context.get("gtm")
            if gtm:
                lines += [
                    "",
                    "GO-TO-MARKET STRATEGY (from GTM Agent — use for revenue model)",
                    f"Pricing Model: {gtm.get('pricing_model', 'N/A')}",
                    f"Pricing Strategy: {gtm.get('pricing_strategy', 'N/A')}",
                    f"Primary Target Segments: {', '.join(gtm.get('primary_target_segments', []))}",
                    f"Customer Acquisition Strategy: {gtm.get('customer_acquisition_strategy', 'N/A')}",
                    f"Launch Timeline: {gtm.get('launch_timeline', 'N/A')}",
                ]
                channels = gtm.get("marketing_channels", [])
                if channels:
                    total_cost = [
                        c.get("estimated_cost", "")
                        for c in channels[:3]
                        if isinstance(c, dict)
                    ]
                    lines.append(f"Top Channel Costs (top 3): {', '.join(total_cost)}")

            # Market size context from DISCOVERY
            discovery = upstream_context.get("discovery")
            if discovery:
                lines += [
                    "",
                    "MARKET CONTEXT (from DISCOVERY Agent)",
                    f"TAM: {discovery.get('total_addressable_market', 'N/A')}",
                    f"SAM: {discovery.get('serviceable_addressable_market', 'N/A')}",
                    f"SOM: {discovery.get('serviceable_obtainable_market', 'N/A')}",
                    f"Growth Rate: {discovery.get('market_growth_rate', 'N/A')}",
                ]

            # Phase 1 dossier context
            phase1 = upstream_context.get("phase1_dossier") or upstream_context
            eval_scores = {
                "market_viability_score": phase1.get("market_viability_score"),
                "feasibility_score": phase1.get("feasibility_score"),
                "scalability_score": phase1.get("scalability_score"),
            }
            if any(v is not None for v in eval_scores.values()):
                lines += [
                    "",
                    "PHASE 1 EVALUATION CONTEXT",
                    f"Market Viability: {eval_scores['market_viability_score']}/10, "
                    f"Feasibility: {eval_scores['feasibility_score']}/10, "
                    f"Scalability: {eval_scores['scalability_score']}/10",
                ]

            # Risk context
            risk = upstream_context.get("risk")
            if risk:
                financial_risks = risk.get("financial_risks", [])
                if financial_risks:
                    lines += ["", "FINANCIAL RISK SIGNALS (from RISK Agent):"]
                    for r in financial_risks:
                        lines.append(f"  - {r}")

        lines += [
            "",
            "=" * 40,
            "Build a comprehensive financial model. Output ONLY valid JSON.",
        ]

        return "\n".join("" if item is None else str(item) for item in lines)

    def _parse_json_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        raw = super()._parse_json_response(raw)
        try:
            validated = FinAgentOutput(**raw)
            return validated.model_dump()
        except ValidationError as exc:
            raise ValueError(
                f"FIN agent output failed schema validation: {exc}"
            ) from exc
