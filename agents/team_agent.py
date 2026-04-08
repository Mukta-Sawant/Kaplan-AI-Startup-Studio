"""
TEAM Agent — Organizational Psychologist.

Assesses team composition, founder-market fit, capability gaps, and
structural risks. Produces a team dynamics report for human mentor review.
Never recommends removing a founder and never uses discriminatory criteria.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from pydantic import ValidationError

from agents.base_agent import BaseAgent
from schemas.team import TeamAgentOutput
from services.claude_client import ClaudeClient, make_team_client


class TeamAgent(BaseAgent):
    """
    Organizational psychologist agent focused on startup team readiness.

    Maps skills to startup needs, assesses founder-market fit, and surfaces
    capability gaps and mentor recommendations.
    """

    agent_name = "team"
    prompt_filename = "team_system_prompt.txt"

    def __init__(self, client: Optional[ClaudeClient] = None) -> None:
        super().__init__(client or make_team_client())

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Format team profiles and startup context as a structured prompt.
        Business model financials are omitted — that is the EVAL domain.
        """
        lines = [
            "STARTUP SUBMISSION — TEAM ASSESSMENT",
            "=" * 40,
            f"Startup Name: {submission_data.get('startup_name', 'N/A')}",
            f"Industry Vertical: {submission_data.get('industry_vertical', 'N/A')}",
            f"Stage: {submission_data.get('stage', 'N/A')}",
            "",
            "PROBLEM DOMAIN",
            submission_data.get("problem_statement") or "Not provided.",
            "",
            "PROPOSED SOLUTION",
            submission_data.get("proposed_solution") or "Not provided.",
            "",
            "TARGET MARKET",
            submission_data.get("target_market") or "Not provided.",
            "",
            "TEAM MEMBERS",
            "=" * 40,
        ]

        team_members = submission_data.get("team_members") or []
        if isinstance(team_members, list):
            for i, member in enumerate(team_members, 1):
                if isinstance(member, dict):
                    lines += [
                        f"Member {i}: {member.get('name') or 'Unknown'}",
                        f"  Role: {member.get('role') or 'N/A'}",
                        f"  Resume: {member.get('resume_text') or 'Not provided.'}",
                        f"  LinkedIn Profile: {member.get('linkedin_url') or 'Not provided.'}",
                    ]
                    if member.get("domain_expertise"):
                        lines.append(f"  Domain Expertise: {member['domain_expertise']}")
                    if member.get("startup_experience"):
                        lines.append(f"  Startup Experience: {member['startup_experience']}")
                    if member.get("commitment_level"):
                        lines.append(f"  Commitment: {member['commitment_level']}")
                    lines.append("")

        lines += [
            "=" * 40,
            "Assess the above team according to your role and output ONLY valid JSON.",
        ]

        return "\n".join("" if item is None else str(item) for item in lines)

    # ------------------------------------------------------------------
    # Output validation
    # ------------------------------------------------------------------

    def _parse_json_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Validate the raw dict against the TeamAgentOutput schema."""
        raw = super()._parse_json_response(raw)
        try:
            validated = TeamAgentOutput(**raw)
            return validated.model_dump()
        except ValidationError as exc:
            raise ValueError(
                f"TEAM agent output failed schema validation: {exc}"
            ) from exc
