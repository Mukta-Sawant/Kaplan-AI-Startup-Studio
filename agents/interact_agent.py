"""
INTERACT Agent — VC Research Analyst.

Identifies information gaps in a startup submission and generates targeted
clarification questions to enable deeper downstream analysis.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ValidationError

from agents.base_agent import BaseAgent
from schemas.interact import InteractAgentOutput
from services.claude_client import ClaudeClient, make_phase2_client


class InteractAgent(BaseAgent):
    """
    VC Research Analyst that surfaces critical unknowns through structured
    clarification questions. Runs first in the Phase 2 parallel batch.
    """

    agent_name = "interact"
    prompt_filename = "interact_system_prompt.txt"

    def __init__(self, client: Optional[ClaudeClient] = None) -> None:
        super().__init__(client or make_phase2_client())

    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> str:
        lines = [
            "STARTUP SUBMISSION — INTERACT ANALYSIS",
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

        team = submission_data.get("team_members")
        if team:
            lines += ["", "TEAM MEMBERS"]
            if isinstance(team, list):
                for member in team:
                    if isinstance(member, dict):
                        lines.append(
                            f"  - {member.get('name', 'Unknown')} "
                            f"({member.get('role', 'N/A')}): "
                            f"{member.get('background', '')}"
                        )
            else:
                lines.append(str(team))

        if upstream_context:
            phase1 = upstream_context.get("phase1_dossier") or upstream_context
            lines += [
                "",
                "PHASE 1 ANALYSIS CONTEXT",
                f"EVAL Scores — Market Viability: {phase1.get('market_viability_score', 'N/A')}, "
                f"Feasibility: {phase1.get('feasibility_score', 'N/A')}, "
                f"Scalability: {phase1.get('scalability_score', 'N/A')}",
            ]
            red_flags = phase1.get("red_flags", [])
            if red_flags:
                lines += ["Red Flags Identified:"]
                for flag in red_flags:
                    lines.append(f"  - {flag}")

        lines += [
            "",
            "=" * 40,
            "Generate targeted clarification questions based on the above submission. Output ONLY valid JSON.",
        ]

        return "\n".join("" if item is None else str(item) for item in lines)

    def _parse_json_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        raw = super()._parse_json_response(raw)
        try:
            validated = InteractAgentOutput(**raw)
            return validated.model_dump()
        except ValidationError as exc:
            raise ValueError(
                f"INTERACT agent output failed schema validation: {exc}"
            ) from exc
