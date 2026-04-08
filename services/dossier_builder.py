"""
Builds the Final Qualification Dossier from EVAL and TEAM agent outputs.

The dossier is the only artefact that human mentors interact with.
It never autonomously approves or rejects a startup.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from schemas.eval import EvalAgentOutput
from schemas.team import TeamAgentOutput

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Conflict detection thresholds
# ---------------------------------------------------------------------------
# A mentor review is flagged when there is a significant divergence between
# the EVAL and TEAM assessments. Two symmetric rules apply:
#
#   Rule A — Eval strong, team weak:
#     eval_average >= EVAL_STRONG_THRESHOLD AND fmf_score <= TEAM_WEAK_THRESHOLD
#
#   Rule B — Team strong, eval weak:
#     eval_average <= EVAL_WEAK_THRESHOLD AND fmf_score >= TEAM_STRONG_THRESHOLD

EVAL_STRONG_THRESHOLD = 8.0
EVAL_WEAK_THRESHOLD = 4.0
TEAM_STRONG_THRESHOLD = 8.0
TEAM_WEAK_THRESHOLD = 4.0


def requires_mentor_review(
    eval_output: EvalAgentOutput,
    team_output: TeamAgentOutput,
) -> bool:
    """
    Determine whether the EVAL and TEAM reports are in significant conflict.

    Returns True when the assessments are substantially divergent, signalling
    that a human mentor should review before any recommendation is shared.
    """
    eval_avg = eval_output.average_score
    fmf = team_output.founder_market_fit_score

    rule_a = eval_avg >= EVAL_STRONG_THRESHOLD and fmf <= TEAM_WEAK_THRESHOLD
    rule_b = eval_avg <= EVAL_WEAK_THRESHOLD and fmf >= TEAM_STRONG_THRESHOLD

    if rule_a:
        logger.info(
            "Mentor review triggered: eval_avg=%.1f >= %.1f but fmf=%d <= %d (Rule A)",
            eval_avg, EVAL_STRONG_THRESHOLD, fmf, TEAM_WEAK_THRESHOLD,
        )
    elif rule_b:
        logger.info(
            "Mentor review triggered: eval_avg=%.1f <= %.1f but fmf=%d >= %d (Rule B)",
            eval_avg, EVAL_WEAK_THRESHOLD, fmf, TEAM_STRONG_THRESHOLD,
        )

    return rule_a or rule_b


def build_dossier_summary(
    eval_output: EvalAgentOutput,
    team_output: TeamAgentOutput,
    mentor_review_required: bool,
) -> str:
    """
    Produce a concise natural-language summary of the dossier for quick scanning.

    This summary is informational only and does not constitute a recommendation.
    """
    eval_avg = eval_output.average_score
    fmf = team_output.founder_market_fit_score
    flags = len(eval_output.red_flags)
    gaps = len(team_output.identified_gaps)

    lines: list[str] = [
        f"Phase 1 qualification assessment completed.",
        f"EVAL scores — Market: {eval_output.market_viability_score}/10, "
        f"Feasibility: {eval_output.feasibility_score}/10, "
        f"Scalability: {eval_output.scalability_score}/10 "
        f"(avg {eval_avg:.1f}/10).",
        f"TEAM assessment — Founder-Market Fit: {fmf}/10.",
    ]

    if flags:
        lines.append(f"{flags} red flag(s) identified by the EVAL agent.")
    if gaps:
        lines.append(f"{gaps} capability gap(s) identified by the TEAM agent.")
    if team_output.recommended_mentors:
        lines.append(
            "Recommended mentor specialisations: "
            + ", ".join(team_output.recommended_mentors[:3])
            + ("…" if len(team_output.recommended_mentors) > 3 else ".")
        )
    if mentor_review_required:
        lines.append(
            "NOTE: Significant divergence between EVAL and TEAM assessments. "
            "Human mentor review is required before this dossier is shared."
        )

    return " ".join(lines)


def build_dossier(
    submission_id: UUID,
    eval_output: EvalAgentOutput,
    team_output: TeamAgentOutput,
) -> dict[str, Any]:
    """
    Merge EVAL and TEAM outputs into the Final Qualification Dossier dict.

    Args:
        submission_id: The submission this dossier belongs to.
        eval_output:   Validated EVAL agent output.
        team_output:   Validated TEAM agent output.

    Returns:
        A dict conforming to the FinalDossier schema.
    """
    mentor_review = requires_mentor_review(eval_output, team_output)
    summary = build_dossier_summary(eval_output, team_output, mentor_review)

    return {
        "submission_id": str(submission_id),
        "phase": "phase1",
        "eval_report": eval_output.model_dump(),
        "team_report": team_output.model_dump(),
        "mentor_review_required": mentor_review,
        "dossier_summary": summary,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
