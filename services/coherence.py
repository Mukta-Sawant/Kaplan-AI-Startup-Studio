"""
Coherence scoring for agent outputs.

A coherence score reflects how well-formed and internally consistent an agent
response is. It is not a measure of the startup's quality — only of whether
the agent output is structurally sound and safe to surface to humans.

Score components (each 0-1, weighted equally):
  1. schema_valid     — the output parsed successfully against the Pydantic schema
  2. sections_filled  — required string fields are non-empty and meaningful
  3. scores_in_range  — numeric scores fall within their declared bounds
  4. consistency      — no obvious internal contradictions (confidence vs flags)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def compute_coherence(output: dict[str, Any], agent_name: str) -> float:
    """
    Compute a coherence score for an agent output dict.

    Args:
        output:     The parsed JSON dict returned by the agent.
        agent_name: "eval" or "team" — selects the scoring profile.

    Returns:
        Float in [0.0, 1.0].  Higher is better.
    """
    checks = []

    if agent_name == "eval":
        checks = _eval_checks(output)
    elif agent_name == "team":
        checks = _team_checks(output)
    else:
        logger.warning("Unknown agent_name %r; returning neutral coherence.", agent_name)
        return 0.5

    passed = sum(1 for ok in checks if ok)
    score = round(passed / len(checks), 4) if checks else 0.0
    logger.debug("Coherence for %s: %.2f (%d/%d checks passed)", agent_name, score, passed, len(checks))
    return score


# ---------------------------------------------------------------------------
# EVAL checks
# ---------------------------------------------------------------------------

def _eval_checks(o: dict[str, Any]) -> list[bool]:
    checks: list[bool] = []

    # 1. Required keys present
    required = {
        "market_viability_score", "feasibility_score", "scalability_score",
        "red_flags", "summary_recommendation", "confidence_level",
    }
    checks.append(required.issubset(o.keys()))

    # 2. Scores in valid range
    for key in ("market_viability_score", "feasibility_score", "scalability_score"):
        val = o.get(key)
        checks.append(isinstance(val, (int, float)) and 1 <= val <= 10)

    # 3. Confidence in range
    conf = o.get("confidence_level")
    checks.append(isinstance(conf, float) and 0.0 <= conf <= 1.0)

    # 4. Non-empty summary
    summary = o.get("summary_recommendation", "")
    checks.append(isinstance(summary, str) and len(summary.strip()) >= 10)

    # 5. red_flags is a list
    checks.append(isinstance(o.get("red_flags"), list))

    # 6. Consistency: if confidence < 0.4, clarification_request should be present
    if isinstance(conf, float) and conf < 0.4:
        checks.append(bool(o.get("clarification_request")))
    else:
        checks.append(True)  # no constraint applies

    return checks


# ---------------------------------------------------------------------------
# TEAM checks
# ---------------------------------------------------------------------------

def _team_checks(o: dict[str, Any]) -> list[bool]:
    checks: list[bool] = []

    # 1. Required keys present
    required = {
        "role_alignment_matrix", "founder_market_fit_score",
        "identified_gaps", "recommended_mentors",
        "team_risk_factors", "confidence_level",
    }
    checks.append(required.issubset(o.keys()))

    # 2. founder_market_fit_score in range
    fmf = o.get("founder_market_fit_score")
    checks.append(isinstance(fmf, (int, float)) and 1 <= fmf <= 10)

    # 3. confidence in range
    conf = o.get("confidence_level")
    checks.append(isinstance(conf, float) and 0.0 <= conf <= 1.0)

    # 4. role_alignment_matrix is a non-empty list
    matrix = o.get("role_alignment_matrix", [])
    checks.append(isinstance(matrix, list) and len(matrix) > 0)

    # 5. Each matrix entry has required keys
    entry_keys = {"member_name", "role", "strengths", "coverage_areas", "gaps"}
    if isinstance(matrix, list):
        checks.append(all(entry_keys.issubset(e.keys()) for e in matrix if isinstance(e, dict)))
    else:
        checks.append(False)

    # 6. identified_gaps is a list
    checks.append(isinstance(o.get("identified_gaps"), list))

    return checks
