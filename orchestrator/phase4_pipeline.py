"""
Phase 4 orchestration pipeline — Moving to Funding.

Execution model:
  Step 1: DECKS — synthesizes all prior phase outputs into 12-slide deck outline
  Step 2: Data-gap re-run (one-time only) — if DECKS identifies a critical gap,
          re-run the missing Phase 2 agent, then re-run DECKS with updated context
  Step 3: VC — uses DECKS narrative to match investors and score fundability

Each step is sequential; each agent gets its own database session.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from agents.decks_agent import DecksAgent
from agents.vc_agent import VCAgent
from models.db import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Maps missing_from_agent names to the Phase 2 agent classes for re-run
_RETRIGGERABLE_AGENTS: dict[str, Any] = {}


def _get_retriggerable_agents() -> dict[str, Any]:
    """Lazy import to avoid circular imports at module load time."""
    if not _RETRIGGERABLE_AGENTS:
        from agents.comp_agent import CompAgent
        from agents.discovery_agent import DiscoveryAgent
        from agents.fin_agent import FinAgent
        from agents.gtm_agent import GTMAgent
        from agents.risk_agent import RiskAgent
        _RETRIGGERABLE_AGENTS.update({
            "comp": CompAgent,
            "discovery": DiscoveryAgent,
            "fin": FinAgent,
            "gtm": GTMAgent,
            "risk": RiskAgent,
        })
    return _RETRIGGERABLE_AGENTS


class Phase4Pipeline:
    """
    Coordinates Phase 4 Moving to Funding agents.

    Step 1: DECKS — synthesizes all prior outputs, identifies data gaps
    Step 2: Optional one-time data-gap re-run of a Phase 2 agent + DECKS re-run
    Step 3: VC — investor matching and fundability scoring

    All agents receive their own database sessions.
    """

    def __init__(
        self,
        decks_agent: DecksAgent | None = None,
        vc_agent: VCAgent | None = None,
    ) -> None:
        self._decks = decks_agent or DecksAgent()
        self._vc = vc_agent or VCAgent()

    async def run(
        self,
        submission_id: UUID,
        submission_data: dict[str, Any],
        db: AsyncSession,
        phase1_dossier: dict[str, Any] | None = None,
        phase2_output: dict[str, Any] | None = None,
        phase3_output: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute Phase 4 sequentially.

        Args:
            submission_id:   UUID of the submission.
            submission_data: Full submission payload dict.
            db:              Active session (not used by agents directly).
            phase1_dossier:  Merged Phase 1 output dict.
            phase2_output:   Merged Phase 2 output dict.
            phase3_output:   Merged Phase 3 output dict.

        Returns:
            Merged Phase 4 output dict ready for PhaseOutput persistence.
        """
        p2 = phase2_output or {}
        p3 = phase3_output or {}

        logger.info("Phase 4 pipeline starting for submission %s", submission_id)

        # Build the full DECKS context from all prior phases
        decks_context = _build_decks_context(phase1_dossier, p2, p3)

        # -------------------------------------------------------------------
        # Step 1: Run DECKS
        # -------------------------------------------------------------------
        logger.info("Phase 4 DECKS agent starting for submission %s", submission_id)
        async with AsyncSessionLocal() as decks_db:
            try:
                decks_result = await self._decks.run(
                    submission_id, submission_data, decks_db, decks_context
                )
            except Exception as exc:
                logger.error(
                    "DECKS agent failed for submission %s: %s", submission_id, exc
                )
                decks_result = _fallback_decks()

        # -------------------------------------------------------------------
        # Step 2: Optional data-gap re-run (one-time only)
        # -------------------------------------------------------------------
        has_retriggered = False
        critical_gaps = [
            g for g in decks_result.get("data_gaps_identified", [])
            if isinstance(g, dict)
            and g.get("trigger_rerun") is True
            and g.get("severity") == "critical"
        ]

        if critical_gaps:
            # Take the first critical gap that names a retriggerable agent
            retriggerable = _get_retriggerable_agents()
            for gap in critical_gaps:
                agent_name = (gap.get("missing_from_agent") or "").lower().strip()
                if agent_name in retriggerable:
                    logger.info(
                        "Phase 4 data-gap re-run: re-running %r agent for submission %s",
                        agent_name, submission_id,
                    )
                    has_retriggered = True
                    agent_instance = retriggerable[agent_name]()

                    # Build upstream context for the re-run agent
                    rerun_upstream = {"phase1_dossier": phase1_dossier or {}, **p2}

                    async with AsyncSessionLocal() as rerun_db:
                        try:
                            refreshed_output = await agent_instance.run(
                                submission_id, submission_data, rerun_db, rerun_upstream
                            )
                            # Update the decks context with refreshed data
                            decks_context[f"phase2_{agent_name}"] = refreshed_output
                            logger.info(
                                "Data-gap re-run of %r succeeded for submission %s.",
                                agent_name, submission_id,
                            )
                        except Exception as exc:
                            logger.error(
                                "Data-gap re-run of %r failed for submission %s: %s",
                                agent_name, submission_id, exc,
                            )

                    # Re-run DECKS with updated context (one time only)
                    logger.info(
                        "Re-running DECKS after data-gap refresh for submission %s", submission_id
                    )
                    async with AsyncSessionLocal() as decks_db2:
                        try:
                            decks_result = await self._decks.run(
                                submission_id, submission_data, decks_db2, decks_context
                            )
                        except Exception as exc:
                            logger.error(
                                "DECKS re-run failed for submission %s: %s",
                                submission_id, exc,
                            )
                    break  # Only re-trigger once, for the first actionable gap

        # -------------------------------------------------------------------
        # Step 3: Run VC — uses DECKS output + fin + risk + phase1 + cust
        # -------------------------------------------------------------------
        vc_context = {
            "decks": decks_result,
            "phase2_fin": p2.get("fin") or {},
            "phase2_risk": p2.get("risk") or {},
            "phase1_dossier": phase1_dossier or {},
            "phase3_cust": p3.get("cust") or {},
        }

        logger.info("Phase 4 VC agent starting for submission %s", submission_id)
        async with AsyncSessionLocal() as vc_db:
            try:
                vc_result = await self._vc.run(
                    submission_id, submission_data, vc_db, vc_context
                )
            except Exception as exc:
                logger.error(
                    "VC agent failed for submission %s: %s", submission_id, exc
                )
                vc_result = _fallback_vc()

        mentor_consultation = vc_result.get("mentor_consultation_required", False)
        logger.info("Phase 4 pipeline complete for submission %s.", submission_id)

        return {
            "phase4_status": "complete",
            "submission_id": str(submission_id),
            "decks": decks_result,
            "vc": vc_result,
            "has_retriggered_data_gap": has_retriggered,
            "mentor_consultation_required": mentor_consultation,
            "agent_statuses": {
                "decks": "success" if "error" not in decks_result else "failed",
                "vc": "success" if "error" not in vc_result else "failed",
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_decks_context(
    phase1_dossier: dict[str, Any] | None,
    p2: dict[str, Any],
    p3: dict[str, Any],
) -> dict[str, Any]:
    return {
        "phase1_dossier": phase1_dossier or {},
        "phase2_comp": p2.get("comp") or {},
        "phase2_interact": p2.get("interact") or {},
        "phase2_discovery": p2.get("discovery") or {},
        "phase2_risk": p2.get("risk") or {},
        "phase2_fin": p2.get("fin") or {},
        "phase2_gtm": p2.get("gtm") or {},
        "phase3_cust": p3.get("cust") or {},
        "phase3_channels": p3.get("channels") or {},
        "phase3_mktg": p3.get("mktg") or {},
    }


# ---------------------------------------------------------------------------
# Fallback outputs
# ---------------------------------------------------------------------------

def _fallback_decks() -> dict[str, Any]:
    return {
        "slide_outline": [],
        "narrative_arc": "DECKS agent failed — investor narrative unavailable.",
        "data_gaps_identified": [
            {
                "gap_description": "DECKS agent failed entirely.",
                "missing_from_agent": "decks",
                "severity": "critical",
                "trigger_rerun": False,
            }
        ],
        "deck_readiness_score": 1,
        "decks_summary": "DECKS agent encountered an error. Manual deck preparation required.",
        "confidence_level": 0.0,
        "clarification_request": "DECKS agent failed. Please rerun Phase 4.",
        "error": "DECKS agent failed",
    }


def _fallback_vc() -> dict[str, Any]:
    return {
        "investor_list": [],
        "outreach_strategy": {
            "recommended_sequence": ["VC agent failed — manual investor research required."],
            "pitch_customization_tips": [],
            "timing_recommendation": "Unknown — VC agent failed.",
            "conference_opportunities": [],
        },
        "fundability_scorecard": {
            "overall_score": 1,
            "team_score": 1,
            "market_score": 1,
            "traction_score": 1,
            "product_score": 1,
            "financial_score": 1,
            "score_breakdown": ["VC agent failed — scoring unavailable."],
            "improvement_recommendations": [],
        },
        "mentor_consultation_required": True,
        "vc_summary": "VC agent encountered an error. Mentor consultation required.",
        "confidence_level": 0.0,
        "clarification_request": "VC agent failed. Please rerun Phase 4.",
        "error": "VC agent failed",
    }
