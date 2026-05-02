"""
DISCOVERY Agent — Industry Consultant.

Conducts rigorous market discovery analysis: TAM/SAM/SOM sizing,
industry trends, regulatory landscape, and market entry barriers.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ValidationError

from agents.base_agent import BaseAgent
from schemas.discovery import DiscoveryAgentOutput
from services.claude_client import ClaudeClient, make_phase2_client


class DiscoveryAgent(BaseAgent):
    """
    Industry Consultant that quantifies the market opportunity and
    characterizes the structural dynamics of the target industry.
    """

    agent_name = "discovery"
    prompt_filename = "discovery_system_prompt.txt"

    def __init__(self, client: Optional[ClaudeClient] = None) -> None:
        super().__init__(client or make_phase2_client())

    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> str:
        lines = [
            "STARTUP SUBMISSION — MARKET DISCOVERY ANALYSIS",
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
            ("COMPETITIVE LANDSCAPE", "competitive_landscape"),
            ("TECHNICAL STATUS", "technical_status"),
        ]
        for heading, key in optional_sections:
            value = submission_data.get(key)
            if value:
                lines += ["", heading, str(value)]

        if upstream_context:
            phase1 = upstream_context.get("phase1_dossier") or upstream_context
            lines += [
                "",
                "PHASE 1 MARKET SIGNALS",
                f"Market Viability Score: {phase1.get('market_viability_score', 'N/A')}",
                f"Scalability Score: {phase1.get('scalability_score', 'N/A')}",
            ]
            red_flags = phase1.get("red_flags", [])
            if red_flags:
                lines += ["Red Flags from EVAL Agent:"]
                for flag in red_flags:
                    lines.append(f"  - {flag}")

        lines += [
            "",
            "=" * 40,
            "Conduct a comprehensive market discovery analysis. Output ONLY valid JSON.",
        ]

        return "\n".join("" if item is None else str(item) for item in lines)

    def _parse_json_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        raw = super()._parse_json_response(raw)
        try:
            validated = DiscoveryAgentOutput(**raw)
            return validated.model_dump()
        except ValidationError as exc:
            raise ValueError(
                f"DISCOVERY agent output failed schema validation: {exc}"
            ) from exc
