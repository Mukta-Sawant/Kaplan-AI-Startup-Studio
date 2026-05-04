"""
MKTG Agent — Marketing Executioner.

Produces a concrete, seed-stage-realistic marketing plan: channel tactics,
8-week content calendar, messaging templates, and KPI targets.

Runs last in Phase 3 (after CUST and CHANNELS), consuming both outputs.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ValidationError

from agents.base_agent import BaseAgent
from schemas.mktg import MktgAgentOutput
from services.claude_client import ClaudeClient, make_phase3_client


class MktgAgent(BaseAgent):
    """
    Marketing Executioner that builds a lean, executable marketing plan
    grounded in the early adopter profile and partner intelligence.
    """

    agent_name = "mktg"
    prompt_filename = "mktg_system_prompt.txt"

    def __init__(self, client: Optional[ClaudeClient] = None) -> None:
        super().__init__(client or make_phase3_client())

    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> str:
        lines = [
            "STARTUP SUBMISSION — MARKETING EXECUTION PLAN",
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
            # CUST output — primary input
            cust = upstream_context.get("cust")
            if cust:
                lines += [
                    "",
                    "CUSTOMER INTELLIGENCE (from CUST Agent — primary input)",
                    f"Early Adopter Profile: {cust.get('early_adopter_profile', 'N/A')}",
                ]
                segments = cust.get("customer_segments", [])
                if segments:
                    lines.append("Customer Segments (priority order):")
                    for seg in segments[:3]:
                        if isinstance(seg, dict):
                            lines.append(
                                f"  - Segment {seg.get('priority_rank', '')}: "
                                f"{seg.get('segment_name', '')} — "
                                f"{seg.get('professional_profile', '')}"
                            )
                            pains = seg.get("pain_points", [])
                            if pains:
                                lines.append(f"    Pain points: {'; '.join(pains[:2])}")
                interview_qs = cust.get("interview_script_suggestions", [])
                if interview_qs:
                    lines.append("Key Customer Pain Themes (from interview scripts):")
                    for q in interview_qs[:3]:
                        lines.append(f"  - {q}")

            # CHANNELS output — partner intel
            channels = upstream_context.get("channels")
            if channels:
                lines += [
                    "",
                    "PARTNER INTELLIGENCE (from CHANNELS Agent)",
                ]
                top_partners = channels.get("outreach_priority_ranking", [])
                if top_partners:
                    lines.append(f"Top Priority Partners: {', '.join(top_partners[:5])}")
                partner_map = channels.get("partner_map", [])
                co_mktg = [
                    p for p in partner_map
                    if isinstance(p, dict) and p.get("partnership_type") == "co-marketing"
                ]
                if co_mktg:
                    lines.append("Co-Marketing Partners Available:")
                    for p in co_mktg[:3]:
                        lines.append(
                            f"  - {p.get('organization_name', '')}: "
                            f"{p.get('shared_audience', '')}"
                        )

            # GTM context — value prop and existing channel thinking
            gtm = upstream_context.get("phase2_gtm") or upstream_context.get("gtm")
            if gtm:
                lines += [
                    "",
                    "GTM CONTEXT (from GTM Agent)",
                    f"Value Proposition: {gtm.get('value_proposition', 'N/A')}",
                    f"Pricing Model: {gtm.get('pricing_model', 'N/A')}",
                    f"Pricing Strategy: {gtm.get('pricing_strategy', 'N/A')}",
                ]
                channels_from_gtm = gtm.get("marketing_channels", [])
                if channels_from_gtm:
                    lines.append("Recommended Channels (from GTM, incorporate or refine):")
                    for ch in channels_from_gtm[:4]:
                        if isinstance(ch, dict):
                            lines.append(
                                f"  - {ch.get('channel', '')} "
                                f"(priority {ch.get('priority', '')}): "
                                f"{ch.get('strategy', '')}"
                            )

        lines += [
            "",
            "=" * 40,
            "Build a lean, executable marketing plan for a seed-stage team. Output ONLY valid JSON.",
        ]

        return "\n".join("" if item is None else str(item) for item in lines)

    def _parse_json_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        raw = super()._parse_json_response(raw)
        try:
            validated = MktgAgentOutput(**raw)
            return validated.model_dump()
        except ValidationError as exc:
            raise ValueError(
                f"MKTG agent output failed schema validation: {exc}"
            ) from exc
