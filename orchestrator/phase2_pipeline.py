"""
Phase 2 orchestration pipeline.

Runs INTERACT, DISCOVERY, COMP, RISK, and GTM agents in parallel via
asyncio.gather for minimum latency, then runs FIN with GTM output as
upstream context (FIN requires GTM pricing/channel data for financial modeling).

Execution model:
  Stage A (parallel): INTERACT + DISCOVERY + COMP + RISK + GTM
  Stage B (sequential): FIN (depends on GTM output)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from agents.comp_agent import CompAgent
from agents.discovery_agent import DiscoveryAgent
from agents.fin_agent import FinAgent
from agents.gtm_agent import GTMAgent
from agents.interact_agent import InteractAgent
from agents.risk_agent import RiskAgent
from models.db import AsyncSessionLocal

logger = logging.getLogger(__name__)


class Phase2Pipeline:
    """
    Coordinates Phase 2 Stage One Analysis agents with maximum parallelism.

    Stage A (parallel, asyncio.gather):
        INTERACT — clarification questions
        DISCOVERY — market sizing and industry analysis
        COMP — competitive landscape
        RISK — risk register
        GTM — go-to-market strategy

    Stage B (after Stage A):
        FIN — financial model (receives GTM + DISCOVERY + RISK as context)

    All agents receive Phase 1 dossier as upstream context.
    Each agent gets its own database session for concurrency safety.
    """

    def __init__(
        self,
        interact_agent: InteractAgent | None = None,
        discovery_agent: DiscoveryAgent | None = None,
        comp_agent: CompAgent | None = None,
        risk_agent: RiskAgent | None = None,
        gtm_agent: GTMAgent | None = None,
        fin_agent: FinAgent | None = None,
    ) -> None:
        self._interact = interact_agent or InteractAgent()
        self._discovery = discovery_agent or DiscoveryAgent()
        self._comp = comp_agent or CompAgent()
        self._risk = risk_agent or RiskAgent()
        self._gtm = gtm_agent or GTMAgent()
        self._fin = fin_agent or FinAgent()

    async def run(
        self,
        submission_id: UUID,
        submission_data: dict[str, Any],
        db: AsyncSession,
        phase1_dossier: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute Phase 2 in two stages for minimum latency.

        Args:
            submission_id:  UUID of the submission.
            submission_data: Full submission payload dict.
            db:             Active async SQLAlchemy session (not directly used
                            by agents — each creates its own session).
            phase1_dossier: Merged Phase 1 output dict (EVAL + TEAM dossier).

        Returns:
            Merged Phase 2 output dict ready for PhaseOutput persistence.
        """
        logger.info(
            "Phase 2 pipeline starting for submission %s (Stage A: 5 parallel agents)",
            submission_id,
        )

        upstream = {"phase1_dossier": phase1_dossier} if phase1_dossier else {}

        # -----------------------------------------------------------------------
        # Stage A: Run 5 agents in parallel — each with its own DB session
        # -----------------------------------------------------------------------
        async with (
            AsyncSessionLocal() as interact_db,
            AsyncSessionLocal() as discovery_db,
            AsyncSessionLocal() as comp_db,
            AsyncSessionLocal() as risk_db,
            AsyncSessionLocal() as gtm_db,
        ):
            results = await asyncio.gather(
                self._interact.run(submission_id, submission_data, interact_db, upstream),
                self._discovery.run(submission_id, submission_data, discovery_db, upstream),
                self._comp.run(submission_id, submission_data, comp_db, upstream),
                self._risk.run(submission_id, submission_data, risk_db, upstream),
                self._gtm.run(submission_id, submission_data, gtm_db, upstream),
                return_exceptions=True,
            )

        interact_result, discovery_result, comp_result, risk_result, gtm_result = results

        # Log any Stage A failures — continue with fallbacks for non-critical agents
        stage_a_outputs: dict[str, Any] = {}
        _handle_result(stage_a_outputs, "interact", interact_result, _fallback_interact())
        _handle_result(stage_a_outputs, "discovery", discovery_result, _fallback_discovery())
        _handle_result(stage_a_outputs, "comp", comp_result, _fallback_comp())
        _handle_result(stage_a_outputs, "risk", risk_result, _fallback_risk())
        _handle_result(stage_a_outputs, "gtm", gtm_result, _fallback_gtm())

        logger.info(
            "Phase 2 Stage A complete for submission %s. Starting FIN agent.",
            submission_id,
        )

        # -----------------------------------------------------------------------
        # Stage B: FIN agent — sequential, after GTM
        # GTM provides pricing/channel context; DISCOVERY provides market sizing;
        # RISK provides financial risk signals.
        # -----------------------------------------------------------------------
        fin_upstream = {
            **upstream,
            "gtm": stage_a_outputs.get("gtm"),
            "discovery": stage_a_outputs.get("discovery"),
            "risk": stage_a_outputs.get("risk"),
        }

        async with AsyncSessionLocal() as fin_db:
            try:
                fin_result = await self._fin.run(
                    submission_id, submission_data, fin_db, fin_upstream
                )
            except Exception as exc:
                logger.error("FIN agent failed for submission %s: %s", submission_id, exc)
                fin_result = _fallback_fin()

        logger.info("Phase 2 pipeline complete for submission %s.", submission_id)

        return {
            "phase2_status": "complete",
            "submission_id": str(submission_id),
            "interact": stage_a_outputs.get("interact"),
            "discovery": stage_a_outputs.get("discovery"),
            "comp": stage_a_outputs.get("comp"),
            "risk": stage_a_outputs.get("risk"),
            "gtm": stage_a_outputs.get("gtm"),
            "fin": fin_result,
            "agent_statuses": {
                "interact": "success" if not isinstance(interact_result, Exception) else "failed",
                "discovery": "success" if not isinstance(discovery_result, Exception) else "failed",
                "comp": "success" if not isinstance(comp_result, Exception) else "failed",
                "risk": "success" if not isinstance(risk_result, Exception) else "failed",
                "gtm": "success" if not isinstance(gtm_result, Exception) else "failed",
                "fin": "success" if not isinstance(fin_result, dict) or "error" not in fin_result else "failed",
            },
        }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _handle_result(
    outputs: dict[str, Any],
    agent_name: str,
    result: Any,
    fallback: dict[str, Any],
) -> None:
    if isinstance(result, Exception):
        logger.error(
            "Phase 2 agent %r failed: %s. Using fallback output.", agent_name, result
        )
        outputs[agent_name] = fallback
    else:
        outputs[agent_name] = result


# ---------------------------------------------------------------------------
# Fallback outputs — used when an agent fails in Stage A
# ---------------------------------------------------------------------------

def _fallback_interact() -> dict[str, Any]:
    return {
        "clarification_questions": [],
        "priority_topics": [],
        "information_gaps": ["INTERACT agent failed — no clarification questions available."],
        "recommended_follow_up_areas": [],
        "interaction_summary": "INTERACT agent encountered an error. Manual review required.",
        "confidence_level": 0.0,
        "clarification_request": "INTERACT agent failed. Please rerun Phase 2.",
    }


def _fallback_discovery() -> dict[str, Any]:
    return {
        "total_addressable_market": "Unknown — DISCOVERY agent failed.",
        "serviceable_addressable_market": "Unknown",
        "serviceable_obtainable_market": "Unknown",
        "market_growth_rate": "Unknown",
        "key_market_trends": [],
        "market_segments": [],
        "regulatory_landscape": "DISCOVERY agent failed — regulatory analysis unavailable.",
        "industry_maturity": "Unknown",
        "market_entry_barriers": [],
        "market_opportunities": [],
        "market_threats": [],
        "discovery_summary": "DISCOVERY agent encountered an error. Human mentor review required.",
        "confidence_level": 0.0,
        "clarification_request": "DISCOVERY agent failed. Please rerun Phase 2.",
    }


def _fallback_comp() -> dict[str, Any]:
    return {
        "direct_competitors": [],
        "indirect_competitors": [],
        "competitive_advantages": [],
        "competitive_disadvantages": ["COMP agent failed — competitive analysis unavailable."],
        "differentiation_factors": [],
        "moat_assessment": "COMP agent failed — moat analysis unavailable.",
        "competitive_positioning": "Unknown",
        "white_space_opportunities": [],
        "competitive_risk_factors": ["COMP agent encountered an error."],
        "overall_competitive_score": 1,
        "comp_summary": "COMP agent encountered an error. Human mentor review required.",
        "confidence_level": 0.0,
        "clarification_request": "COMP agent failed. Please rerun Phase 2.",
    }


def _fallback_risk() -> dict[str, Any]:
    return {
        "risk_register": [],
        "overall_risk_score": 10,
        "critical_risks": ["RISK agent failed — risk analysis unavailable."],
        "market_risks": [],
        "technical_risks": [],
        "regulatory_risks": [],
        "financial_risks": [],
        "operational_risks": [],
        "risk_mitigation_summary": "RISK agent encountered an error. Human mentor review required.",
        "go_no_go_recommendation": "conditional_go",
        "confidence_level": 0.0,
        "clarification_request": "RISK agent failed. Please rerun Phase 2.",
    }


def _fallback_gtm() -> dict[str, Any]:
    return {
        "primary_target_segments": [],
        "ideal_customer_profile": "GTM agent failed — ICP analysis unavailable.",
        "value_proposition": "GTM agent failed.",
        "pricing_model": "unknown",
        "pricing_strategy": "GTM agent failed — pricing analysis unavailable.",
        "marketing_channels": [],
        "sales_strategy": "GTM agent failed — sales strategy unavailable.",
        "launch_timeline": "GTM agent failed — timeline unavailable.",
        "key_partnerships": [],
        "customer_acquisition_strategy": "GTM agent failed.",
        "gtm_risk_factors": ["GTM agent encountered an error."],
        "success_metrics": [],
        "gtm_summary": "GTM agent encountered an error. Human mentor review required.",
        "confidence_level": 0.0,
        "clarification_request": "GTM agent failed. Please rerun Phase 2.",
    }


def _fallback_fin() -> dict[str, Any]:
    return {
        "revenue_projections": [],
        "burn_rate_monthly": "Unknown — FIN agent failed.",
        "runway_months": 0,
        "funding_ask": "Unknown",
        "pre_money_valuation": "Unknown",
        "use_of_funds": [],
        "unit_economics": {
            "customer_acquisition_cost": "Unknown",
            "lifetime_value": "Unknown",
            "ltv_cac_ratio": "Unknown",
            "payback_period_months": 0,
            "gross_margin_percent": "Unknown",
        },
        "key_financial_assumptions": [],
        "financial_risk_factors": ["FIN agent encountered an error."],
        "break_even_timeline": "Unknown",
        "investment_readiness_score": 1,
        "fin_summary": "FIN agent encountered an error. Human mentor review required.",
        "confidence_level": 0.0,
        "clarification_request": "FIN agent failed. Please rerun Phase 2.",
    }
