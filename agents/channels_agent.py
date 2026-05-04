"""
CHANNELS Agent — Alliances Executive.

Maps distribution partners, integration allies, and co-marketing partners.
Explicitly filters out all competitors identified by the COMP agent.

Runs in Phase 3 Stage B (after CUST, before MKTG).
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ValidationError

from agents.base_agent import BaseAgent
from schemas.channels import ChannelsAgentOutput
from services.claude_client import ClaudeClient, make_phase3_client


class ChannelsAgent(BaseAgent):
    """
    Alliances Executive that identifies distribution and partnership channels,
    excluding all organizations already listed as competitors by COMP.
    """

    agent_name = "channels"
    prompt_filename = "channels_system_prompt.txt"

    def __init__(self, client: Optional[ClaudeClient] = None) -> None:
        super().__init__(client or make_phase3_client())

    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> str:
        lines = [
            "STARTUP SUBMISSION — PARTNERSHIP & CHANNEL ANALYSIS",
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
            # COMP output — competitors to exclude from partner map
            comp = upstream_context.get("phase2_comp") or upstream_context.get("comp")
            if comp:
                direct = comp.get("direct_competitors", [])
                indirect = comp.get("indirect_competitors", [])
                if direct or indirect:
                    lines += ["", "COMPETITORS TO EXCLUDE FROM PARTNER MAP (from COMP Agent)"]
                    lines.append("Direct Competitors (NEVER list as partners):")
                    for c in direct:
                        if isinstance(c, dict):
                            lines.append(f"  - {c.get('name', '')}")
                    lines.append("Indirect Competitors (NEVER list as partners):")
                    for c in indirect:
                        if isinstance(c, dict):
                            lines.append(f"  - {c.get('name', '')}")
                lines += [
                    "",
                    "COMPETITIVE CONTEXT",
                    f"Competitive Positioning: {comp.get('competitive_positioning', 'N/A')}",
                ]
                key_partnerships = comp.get("white_space_opportunities", [])
                if key_partnerships:
                    lines.append("White Space Opportunities (may suggest partner categories):")
                    for w in key_partnerships[:3]:
                        lines.append(f"  - {w}")

            # GTM target segments — drives partner audience matching
            gtm = upstream_context.get("phase2_gtm") or upstream_context.get("gtm")
            if gtm:
                lines += [
                    "",
                    "TARGET SEGMENTS (from GTM Agent — use for partner audience matching)",
                    f"Primary Segments: {', '.join(gtm.get('primary_target_segments', []))}",
                    f"Ideal Customer Profile: {gtm.get('ideal_customer_profile', 'N/A')}",
                    f"Existing Key Partnerships Identified: {', '.join(gtm.get('key_partnerships', []))}",
                ]

            # CUST customer profile — drives partner audience matching
            cust = upstream_context.get("cust")
            if cust:
                lines += [
                    "",
                    "EARLY ADOPTER PROFILE (from CUST Agent)",
                    f"Early Adopter: {cust.get('early_adopter_profile', 'N/A')}",
                ]
                segments = cust.get("customer_segments", [])
                if segments:
                    lines.append("Customer Segments:")
                    for seg in segments[:3]:
                        if isinstance(seg, dict):
                            lines.append(
                                f"  - {seg.get('segment_name', '')} "
                                f"(priority {seg.get('priority_rank', '')}): "
                                f"{seg.get('professional_profile', '')}"
                            )

        lines += [
            "",
            "=" * 40,
            "Map distribution partners and allies. Exclude all listed competitors. Output ONLY valid JSON.",
        ]

        return "\n".join("" if item is None else str(item) for item in lines)

    def _parse_json_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        raw = super()._parse_json_response(raw)
        try:
            validated = ChannelsAgentOutput(**raw)
            # Post-validation safety: strip any entry with is_competitor=True
            validated.partner_map = [p for p in validated.partner_map if not p.is_competitor]
            return validated.model_dump()
        except ValidationError as exc:
            raise ValueError(
                f"CHANNELS agent output failed schema validation: {exc}"
            ) from exc
