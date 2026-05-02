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
        agent_name: agent identifier string — selects the scoring profile.

    Returns:
        Float in [0.0, 1.0].  Higher is better.
    """
    checks = []

    if agent_name == "eval":
        checks = _eval_checks(output)
    elif agent_name == "team":
        checks = _team_checks(output)
    elif agent_name == "interact":
        checks = _interact_checks(output)
    elif agent_name == "discovery":
        checks = _discovery_checks(output)
    elif agent_name == "comp":
        checks = _comp_checks(output)
    elif agent_name == "risk":
        checks = _risk_checks(output)
    elif agent_name == "gtm":
        checks = _gtm_checks(output)
    elif agent_name == "fin":
        checks = _fin_checks(output)
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


# ---------------------------------------------------------------------------
# INTERACT checks
# ---------------------------------------------------------------------------

def _interact_checks(o: dict[str, Any]) -> list[bool]:
    checks: list[bool] = []

    required = {
        "clarification_questions", "priority_topics", "information_gaps",
        "recommended_follow_up_areas", "interaction_summary", "confidence_level",
    }
    checks.append(required.issubset(o.keys()))

    questions = o.get("clarification_questions", [])
    checks.append(isinstance(questions, list) and len(questions) >= 1)

    conf = o.get("confidence_level")
    checks.append(isinstance(conf, float) and 0.0 <= conf <= 1.0)

    summary = o.get("interaction_summary", "")
    checks.append(isinstance(summary, str) and len(summary.strip()) >= 10)

    checks.append(isinstance(o.get("priority_topics"), list))
    checks.append(isinstance(o.get("information_gaps"), list))

    return checks


# ---------------------------------------------------------------------------
# DISCOVERY checks
# ---------------------------------------------------------------------------

def _discovery_checks(o: dict[str, Any]) -> list[bool]:
    checks: list[bool] = []

    required = {
        "total_addressable_market", "serviceable_addressable_market",
        "serviceable_obtainable_market", "market_growth_rate",
        "key_market_trends", "regulatory_landscape",
        "industry_maturity", "discovery_summary", "confidence_level",
    }
    checks.append(required.issubset(o.keys()))

    tam = o.get("total_addressable_market", "")
    checks.append(isinstance(tam, str) and len(tam.strip()) >= 3)

    conf = o.get("confidence_level")
    checks.append(isinstance(conf, float) and 0.0 <= conf <= 1.0)

    checks.append(isinstance(o.get("key_market_trends"), list))
    checks.append(isinstance(o.get("market_segments"), list))

    summary = o.get("discovery_summary", "")
    checks.append(isinstance(summary, str) and len(summary.strip()) >= 10)

    maturity_values = {"emerging", "growth", "mature", "declining"}
    checks.append(o.get("industry_maturity", "").lower() in maturity_values)

    return checks


# ---------------------------------------------------------------------------
# COMP checks
# ---------------------------------------------------------------------------

def _comp_checks(o: dict[str, Any]) -> list[bool]:
    checks: list[bool] = []

    required = {
        "direct_competitors", "indirect_competitors",
        "competitive_advantages", "moat_assessment",
        "competitive_positioning", "overall_competitive_score",
        "comp_summary", "confidence_level",
    }
    checks.append(required.issubset(o.keys()))

    score = o.get("overall_competitive_score")
    checks.append(isinstance(score, (int, float)) and 1 <= score <= 10)

    conf = o.get("confidence_level")
    checks.append(isinstance(conf, float) and 0.0 <= conf <= 1.0)

    checks.append(isinstance(o.get("direct_competitors"), list))
    checks.append(isinstance(o.get("indirect_competitors"), list))

    moat = o.get("moat_assessment", "")
    checks.append(isinstance(moat, str) and len(moat.strip()) >= 10)

    summary = o.get("comp_summary", "")
    checks.append(isinstance(summary, str) and len(summary.strip()) >= 10)

    return checks


# ---------------------------------------------------------------------------
# RISK checks
# ---------------------------------------------------------------------------

def _risk_checks(o: dict[str, Any]) -> list[bool]:
    checks: list[bool] = []

    required = {
        "risk_register", "overall_risk_score", "critical_risks",
        "risk_mitigation_summary", "go_no_go_recommendation", "confidence_level",
    }
    checks.append(required.issubset(o.keys()))

    risk_score = o.get("overall_risk_score")
    checks.append(isinstance(risk_score, (int, float)) and 1 <= risk_score <= 10)

    conf = o.get("confidence_level")
    checks.append(isinstance(conf, float) and 0.0 <= conf <= 1.0)

    register = o.get("risk_register", [])
    checks.append(isinstance(register, list))

    valid_recommendations = {
        "conditional_go", "proceed_with_caution", "high_risk_proceed", "do_not_proceed"
    }
    checks.append(o.get("go_no_go_recommendation", "") in valid_recommendations)

    summary = o.get("risk_mitigation_summary", "")
    checks.append(isinstance(summary, str) and len(summary.strip()) >= 10)

    return checks


# ---------------------------------------------------------------------------
# GTM checks
# ---------------------------------------------------------------------------

def _gtm_checks(o: dict[str, Any]) -> list[bool]:
    checks: list[bool] = []

    required = {
        "primary_target_segments", "ideal_customer_profile",
        "value_proposition", "pricing_model", "pricing_strategy",
        "marketing_channels", "sales_strategy", "launch_timeline",
        "gtm_summary", "confidence_level",
    }
    checks.append(required.issubset(o.keys()))

    conf = o.get("confidence_level")
    checks.append(isinstance(conf, float) and 0.0 <= conf <= 1.0)

    checks.append(isinstance(o.get("primary_target_segments"), list) and len(o.get("primary_target_segments", [])) > 0)
    checks.append(isinstance(o.get("marketing_channels"), list))

    icp = o.get("ideal_customer_profile", "")
    checks.append(isinstance(icp, str) and len(icp.strip()) >= 10)

    summary = o.get("gtm_summary", "")
    checks.append(isinstance(summary, str) and len(summary.strip()) >= 10)

    checks.append(isinstance(o.get("key_partnerships"), list))
    checks.append(isinstance(o.get("gtm_risk_factors"), list))

    return checks


# ---------------------------------------------------------------------------
# FIN checks
# ---------------------------------------------------------------------------

def _fin_checks(o: dict[str, Any]) -> list[bool]:
    checks: list[bool] = []

    required = {
        "revenue_projections", "burn_rate_monthly", "runway_months",
        "funding_ask", "use_of_funds", "unit_economics",
        "investment_readiness_score", "fin_summary", "confidence_level",
    }
    checks.append(required.issubset(o.keys()))

    inv_score = o.get("investment_readiness_score")
    checks.append(isinstance(inv_score, (int, float)) and 1 <= inv_score <= 10)

    conf = o.get("confidence_level")
    checks.append(isinstance(conf, float) and 0.0 <= conf <= 1.0)

    projections = o.get("revenue_projections", [])
    checks.append(isinstance(projections, list) and len(projections) >= 1)

    unit_econ = o.get("unit_economics", {})
    unit_keys = {"customer_acquisition_cost", "lifetime_value", "ltv_cac_ratio", "payback_period_months", "gross_margin_percent"}
    checks.append(isinstance(unit_econ, dict) and unit_keys.issubset(unit_econ.keys()))

    runway = o.get("runway_months")
    checks.append(isinstance(runway, int) and runway >= 0)

    summary = o.get("fin_summary", "")
    checks.append(isinstance(summary, str) and len(summary.strip()) >= 10)

    return checks
