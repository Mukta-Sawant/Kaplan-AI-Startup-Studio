"""
CUST Agent — Market Strategy Expert.

Analyzes DISCOVERY market research and GTM segments to pinpoint early adopters,
produce outreach target profiles (no PII), and craft customer interview scripts.

Runs first in Phase 3 (Stage A), before CHANNELS and MKTG.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ValidationError

from agents.base_agent import BaseAgent
from schemas.cust import CustAgentOutput
from services.claude_client import ClaudeClient, make_phase3_client


class CustAgent(BaseAgent):
    """
    Market Strategy Expert that identifies early adopter profiles and
    outreach targets from upstream market discovery and GTM data.
    """

    agent_name = "cust"
    prompt_filename = "cust_system_prompt.txt"

    def __init__(self, client: Optional[ClaudeClient] = None) -> None:
        super().__init__(client or make_phase3_client())

    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> str:
        lines = [
            "STARTUP SUBMISSION — CUSTOMER DISCOVERY ANALYSIS",
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
        ]
        for heading, key in optional_sections:
            value = submission_data.get(key)
            if value:
                lines += ["", heading, str(value)]

        if upstream_context:
            # DISCOVERY market research
            discovery = upstream_context.get("phase2_discovery") or upstream_context.get("discovery")
            if discovery:
                lines += [
                    "",
                    "MARKET RESEARCH (from DISCOVERY Agent — primary input)",
                    f"TAM: {discovery.get('total_addressable_market', 'N/A')}",
                    f"SAM: {discovery.get('serviceable_addressable_market', 'N/A')}",
                    f"SOM: {discovery.get('serviceable_obtainable_market', 'N/A')}",
                    f"Market Growth Rate: {discovery.get('market_growth_rate', 'N/A')}",
                    f"Industry Maturity: {discovery.get('industry_maturity', 'N/A')}",
                ]
                segments = discovery.get("market_segments", [])
                if segments:
                    lines.append("Market Segments:")
                    for seg in segments[:5]:
                        if isinstance(seg, dict):
                            lines.append(
                                f"  - {seg.get('segment_name', '')}: "
                                f"{seg.get('estimated_size', '')} — {seg.get('accessibility', '')}"
                            )
                trends = discovery.get("key_market_trends", [])
                if trends:
                    lines.append("Key Market Trends:")
                    for t in trends[:5]:
                        lines.append(f"  - {t}")

            # GTM segments
            gtm = upstream_context.get("phase2_gtm") or upstream_context.get("gtm")
            if gtm:
                lines += [
                    "",
                    "GO-TO-MARKET CONTEXT (from GTM Agent)",
                    f"Primary Target Segments: {', '.join(gtm.get('primary_target_segments', []))}",
                    f"Ideal Customer Profile: {gtm.get('ideal_customer_profile', 'N/A')}",
                    f"Value Proposition: {gtm.get('value_proposition', 'N/A')}",
                    f"Customer Acquisition Strategy: {gtm.get('customer_acquisition_strategy', 'N/A')}",
                ]

            # Phase 1 context
            phase1 = upstream_context.get("phase1_dossier") or {}
            if phase1:
                lines += [
                    "",
                    "PHASE 1 CONTEXT",
                    f"Market Viability Score: {phase1.get('market_viability_score', 'N/A')}/10",
                    f"Industry: {submission_data.get('industry_vertical', 'N/A')}",
                ]
                red_flags = phase1.get("red_flags", [])
                if red_flags:
                    lines.append("Phase 1 Red Flags:")
                    for f in red_flags[:3]:
                        lines.append(f"  - {f}")

        lines += [
            "",
            "=" * 40,
            "Identify early adopters and outreach targets. Output ONLY valid JSON.",
        ]

        return "\n".join("" if item is None else str(item) for item in lines)

    def _parse_json_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        raw = super()._parse_json_response(raw)
        try:
            validated = CustAgentOutput(**raw)
            return validated.model_dump()
        except ValidationError as exc:
            raise ValueError(
                f"CUST agent output failed schema validation: {exc}"
            ) from exc
