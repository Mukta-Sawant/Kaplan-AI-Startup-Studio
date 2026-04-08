"""
Phase 1 orchestration pipeline.

Runs EVAL and TEAM agents in parallel and merges their outputs into a
Final Qualification Dossier. Handles partial failures gracefully and
triggers clarification state when the EVAL agent's confidence is low.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from agents.eval_agent import EvalAgent
from agents.team_agent import TeamAgent
from models.db import AsyncSessionLocal
from schemas.eval import EvalAgentOutput
from schemas.team import TeamAgentOutput
from services.dossier_builder import build_dossier

logger = logging.getLogger(__name__)


class Phase1Pipeline:
    """
    Coordinates the parallel execution of the EVAL and TEAM agents for Phase 1.

    Usage::

        pipeline = Phase1Pipeline()
        result = await pipeline.run(submission_id, submission_data, db)
    """

    def __init__(
        self,
        eval_agent: EvalAgent | None = None,
        team_agent: TeamAgent | None = None,
    ) -> None:
        self._eval_agent = eval_agent or EvalAgent()
        self._team_agent = team_agent or TeamAgent()

    async def run(
        self,
        submission_id: UUID,
        submission_data: dict[str, Any],
        db: AsyncSession,
    ) -> dict[str, Any]:
        """
        Execute Phase 1: run EVAL and TEAM agents in parallel.

        Args:
            submission_id:   UUID of the submission being evaluated.
            submission_data: Full submission payload dict.
            db:              Active async SQLAlchemy session.

        Returns:
            A dossier dict ready to be persisted as a PhaseOutput.

        Raises:
            RuntimeError: If both agents fail simultaneously.
        """
        logger.info("Phase 1 pipeline starting for submission %s", submission_id)

        # Each agent gets its own session — SQLAlchemy async sessions are not
        # safe for concurrent use, so sharing one session across asyncio.gather
        # causes "transaction is closed" / commit-in-progress errors.
        async with AsyncSessionLocal() as eval_db, AsyncSessionLocal() as team_db:
            eval_task = asyncio.create_task(
                self._eval_agent.run(submission_id, submission_data, eval_db)
            )
            team_task = asyncio.create_task(
                self._team_agent.run(submission_id, submission_data, team_db)
            )
            results = await asyncio.gather(eval_task, team_task, return_exceptions=True)

        eval_result, team_result = results

        eval_failed = isinstance(eval_result, Exception)
        team_failed = isinstance(team_result, Exception)

        if eval_failed and team_failed:
            raise RuntimeError(
                f"Both agents failed. EVAL: {eval_result}. TEAM: {team_result}."
            )

        if eval_failed:
            logger.error("EVAL agent failed: %s. Using fallback.", eval_result)
            eval_output = _fallback_eval_output()
        else:
            eval_output = EvalAgentOutput(**eval_result)

        if team_failed:
            logger.error("TEAM agent failed: %s. Using fallback.", team_result)
            team_output = _fallback_team_output()
        else:
            team_output = TeamAgentOutput(**team_result)

        if eval_output.confidence_level < 0.5:
            logger.info(
                "EVAL confidence %.2f < 0.5 — flagging clarification_needed.",
                eval_output.confidence_level,
            )
            dossier = build_dossier(submission_id, eval_output, team_output)
            dossier["phase1_status"] = "clarification_needed"
            dossier["clarification_request"] = eval_output.clarification_request
        else:
            dossier = build_dossier(submission_id, eval_output, team_output)
            dossier["phase1_status"] = "complete"

        logger.info(
            "Phase 1 pipeline complete for submission %s. mentor_review=%s",
            submission_id,
            dossier.get("mentor_review_required"),
        )
        return dossier


# ---------------------------------------------------------------------------
# Fallback outputs used when one agent fails (partial failure handling)
# ---------------------------------------------------------------------------

def _fallback_eval_output() -> EvalAgentOutput:
    return EvalAgentOutput(
        market_viability_score=1,
        feasibility_score=1,
        scalability_score=1,
        red_flags=["EVAL agent failed — scores are placeholder values only."],
        summary_recommendation=(
            "EVAL agent encountered an error. Human mentor review is required "
            "before any assessment is made."
        ),
        confidence_level=0.0,
        clarification_request="EVAL agent failed. Please rerun Phase 1.",
    )


def _fallback_team_output() -> TeamAgentOutput:
    return TeamAgentOutput(
        role_alignment_matrix=[],
        founder_market_fit_score=1,
        identified_gaps=["TEAM agent failed — gaps are placeholder values only."],
        recommended_mentors=[],
        team_risk_factors=["TEAM agent encountered an error."],
        confidence_level=0.0,
    )
