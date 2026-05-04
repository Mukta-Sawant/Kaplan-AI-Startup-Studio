"""
Phase 3 orchestration pipeline — Stage Two Engagement.

Execution model:
  Stage A (sequential): CUST — needs DISCOVERY + GTM from Phase 2
                         Retried up to 3 times if confidence < 0.4
  Stage B1 (sequential): CHANNELS — needs CUST output + COMP from Phase 2
  Stage B2 (sequential): MKTG — needs CUST + CHANNELS output + GTM from Phase 2

CHANNELS runs before MKTG because MKTG consumes CHANNELS partner intelligence.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from agents.channels_agent import ChannelsAgent
from agents.cust_agent import CustAgent
from agents.mktg_agent import MktgAgent
from models.db import AsyncSessionLocal

logger = logging.getLogger(__name__)

MAX_CUST_ATTEMPTS = 3
CUST_LOW_CONFIDENCE_THRESHOLD = 0.4


class Phase3Pipeline:
    """
    Coordinates Phase 3 Stage Two Engagement agents.

    Stage A: CUST (sequential, with retry loop for low-confidence outputs)
    Stage B1: CHANNELS (sequential, needs CUST output)
    Stage B2: MKTG (sequential, needs CUST + CHANNELS output)

    All agents receive their own database session.
    """

    def __init__(
        self,
        cust_agent: CustAgent | None = None,
        channels_agent: ChannelsAgent | None = None,
        mktg_agent: MktgAgent | None = None,
    ) -> None:
        self._cust = cust_agent or CustAgent()
        self._channels = channels_agent or ChannelsAgent()
        self._mktg = mktg_agent or MktgAgent()

    async def run(
        self,
        submission_id: UUID,
        submission_data: dict[str, Any],
        db: AsyncSession,
        phase1_dossier: dict[str, Any] | None = None,
        phase2_output: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute Phase 3 in sequential stages.

        Args:
            submission_id:    UUID of the submission.
            submission_data:  Full submission payload dict.
            db:               Active session (not used by agents directly).
            phase1_dossier:   Merged Phase 1 output dict.
            phase2_output:    Merged Phase 2 output dict (required for DISCOVERY/GTM/COMP context).

        Returns:
            Merged Phase 3 output dict ready for PhaseOutput persistence.
        """
        p2 = phase2_output or {}
        discovery = p2.get("discovery") or {}
        gtm = p2.get("gtm") or {}
        comp = p2.get("comp") or {}

        logger.info("Phase 3 pipeline starting for submission %s", submission_id)

        # -------------------------------------------------------------------
        # Stage A: CUST — with confidence retry loop (max 3 attempts)
        # -------------------------------------------------------------------
        cust_context = {
            "phase1_dossier": phase1_dossier or {},
            "phase2_discovery": discovery,
            "phase2_gtm": gtm,
        }

        cust_result: dict[str, Any] = _fallback_cust()
        mentor_intervention_required = False
        cust_attempt = 0

        for attempt in range(1, MAX_CUST_ATTEMPTS + 1):
            cust_attempt = attempt
            logger.info(
                "Phase 3 CUST agent attempt %d/%d for submission %s",
                attempt, MAX_CUST_ATTEMPTS, submission_id,
            )
            async with AsyncSessionLocal() as cust_db:
                try:
                    cust_result = await self._cust.run(
                        submission_id, submission_data, cust_db, cust_context
                    )
                except Exception as exc:
                    logger.error(
                        "CUST agent attempt %d failed for submission %s: %s",
                        attempt, submission_id, exc,
                    )
                    cust_result = _fallback_cust()

            confidence = cust_result.get("confidence_level", 0.0)
            if confidence >= CUST_LOW_CONFIDENCE_THRESHOLD:
                logger.info(
                    "CUST agent succeeded with confidence=%.2f on attempt %d",
                    confidence, attempt,
                )
                break

            if attempt < MAX_CUST_ATTEMPTS:
                logger.warning(
                    "CUST confidence=%.2f below threshold=%.2f. Retrying (%d/%d).",
                    confidence, CUST_LOW_CONFIDENCE_THRESHOLD, attempt, MAX_CUST_ATTEMPTS,
                )
            else:
                logger.error(
                    "CUST agent confidence=%.2f still below threshold after %d attempts. "
                    "Flagging mentor_intervention_required.",
                    confidence, MAX_CUST_ATTEMPTS,
                )
                mentor_intervention_required = True

        # -------------------------------------------------------------------
        # Stage B1: CHANNELS — needs CUST + COMP + GTM
        # -------------------------------------------------------------------
        channels_context = {
            "phase2_comp": comp,
            "phase2_gtm": gtm,
            "cust": cust_result,
        }

        logger.info("Phase 3 CHANNELS agent starting for submission %s", submission_id)
        async with AsyncSessionLocal() as channels_db:
            try:
                channels_result = await self._channels.run(
                    submission_id, submission_data, channels_db, channels_context
                )
            except Exception as exc:
                logger.error(
                    "CHANNELS agent failed for submission %s: %s", submission_id, exc
                )
                channels_result = _fallback_channels()

        # -------------------------------------------------------------------
        # Stage B2: MKTG — needs CUST + CHANNELS + GTM
        # -------------------------------------------------------------------
        mktg_context = {
            "cust": cust_result,
            "channels": channels_result,
            "phase2_gtm": gtm,
        }

        logger.info("Phase 3 MKTG agent starting for submission %s", submission_id)
        async with AsyncSessionLocal() as mktg_db:
            try:
                mktg_result = await self._mktg.run(
                    submission_id, submission_data, mktg_db, mktg_context
                )
            except Exception as exc:
                logger.error(
                    "MKTG agent failed for submission %s: %s", submission_id, exc
                )
                mktg_result = _fallback_mktg()

        logger.info("Phase 3 pipeline complete for submission %s.", submission_id)

        return {
            "phase3_status": "complete",
            "submission_id": str(submission_id),
            "cust": cust_result,
            "channels": channels_result,
            "mktg": mktg_result,
            "mentor_intervention_required": mentor_intervention_required,
            "cust_attempts": cust_attempt,
            "agent_statuses": {
                "cust": "success" if "error" not in cust_result else "failed",
                "channels": "success" if "error" not in channels_result else "failed",
                "mktg": "success" if "error" not in mktg_result else "failed",
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Fallback outputs
# ---------------------------------------------------------------------------

def _fallback_cust() -> dict[str, Any]:
    return {
        "customer_segments": [],
        "early_adopter_profile": "CUST agent failed — early adopter profile unavailable.",
        "outreach_list": [],
        "interview_script_suggestions": [],
        "cust_summary": "CUST agent encountered an error. Manual customer discovery required.",
        "confidence_level": 0.0,
        "clarification_request": "CUST agent failed. Please rerun Phase 3.",
        "error": "CUST agent failed",
    }


def _fallback_channels() -> dict[str, Any]:
    return {
        "partner_map": [],
        "partnership_types_breakdown": {},
        "outreach_priority_ranking": [],
        "partnership_gaps": ["CHANNELS agent failed — partnership analysis unavailable."],
        "channels_summary": "CHANNELS agent encountered an error. Manual partner mapping required.",
        "confidence_level": 0.0,
        "clarification_request": "CHANNELS agent failed. Please rerun Phase 3.",
        "error": "CHANNELS agent failed",
    }


def _fallback_mktg() -> dict[str, Any]:
    return {
        "marketing_plan": [],
        "content_calendar": [],
        "messaging_templates": [],
        "kpi_targets": [],
        "mktg_summary": "MKTG agent encountered an error. Manual marketing plan required.",
        "confidence_level": 0.0,
        "clarification_request": "MKTG agent failed. Please rerun Phase 3.",
        "error": "MKTG agent failed",
    }
