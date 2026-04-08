"""
EVAL Agent — VC Seed-Stage Analyst.

Assesses market viability, feasibility, and scalability of a startup submission.
Produces a structured qualification report with scores and red flags.
Never autonomously approves or rejects a startup.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from pydantic import ValidationError

from agents.base_agent import BaseAgent
from schemas.eval import EvalAgentOutput
from services.claude_client import ClaudeClient, make_eval_client


class EvalAgent(BaseAgent):
    """
    Rigorous VC seed-stage analyst agent.

    Applies a Kaplan rubric to score market viability, feasibility, and
    scalability. Triggers a clarification request when confidence is low.
    """

    agent_name = "eval"
    prompt_filename = "eval_system_prompt.txt"

    def __init__(self, client: Optional[ClaudeClient] = None) -> None:
        super().__init__(client or make_eval_client())

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Format the submission's business and market data as a structured prompt.
        Team member details are omitted — that is the TEAM agent's domain.
        """
        lines = [
            "STARTUP SUBMISSION — EVAL ASSESSMENT",
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

        docs = submission_data.get("supporting_documents")
        if docs:
            lines += ["", "SUPPORTING DOCUMENTS"]
            if isinstance(docs, list):
                for doc in docs:
                    lines.append(f"  - {doc}")
            else:
                lines.append(str(docs))

        lines += [
            "",
            "=" * 40,
            "Evaluate the above submission according to your role and output ONLY valid JSON.",
        ]

        return "\n".join("" if item is None else str(item) for item in lines)

    # ------------------------------------------------------------------
    # Output validation
    # ------------------------------------------------------------------

    def _parse_json_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Validate the raw dict against the EvalAgentOutput schema."""
        raw = super()._parse_json_response(raw)
        try:
            validated = EvalAgentOutput(**raw)
            return validated.model_dump()
        except ValidationError as exc:
            raise ValueError(
                f"EVAL agent output failed schema validation: {exc}"
            ) from exc
