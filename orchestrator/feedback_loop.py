"""
Feedback loop orchestrator.

Accepts human feedback entries and optionally triggers agent reruns.
All rerun history is preserved — old runs are never deleted.
"""

from __future__ import annotations

import logging
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.feedback_entry import FeedbackEntry
from models.submission import Submission
from orchestrator.hoster import Hoster
from orchestrator.pipeline import Phase1Pipeline
from schemas.feedback import FeedbackCreate

logger = logging.getLogger(__name__)

RerunScope = Literal["eval", "team", "phase1"]


class FeedbackLoop:
    """
    Processes feedback entries and manages conditional agent reruns.

    Reruns are scoped:
    - "eval":   re-run only the EVAL agent
    - "team":   re-run only the TEAM agent
    - "phase1": re-run the full Phase 1 pipeline
    """

    def __init__(
        self,
        pipeline: Phase1Pipeline | None = None,
        hoster: Hoster | None = None,
    ) -> None:
        self._pipeline = pipeline or Phase1Pipeline()
        self._hoster = hoster or Hoster()

    async def process(
        self,
        feedback_data: FeedbackCreate,
        db: AsyncSession,
    ) -> FeedbackEntry:
        """
        Record feedback and trigger a rerun if requested.

        Args:
            feedback_data: Validated feedback payload.
            db:            Active async session.

        Returns:
            The persisted FeedbackEntry record.
        """
        entry = FeedbackEntry(
            submission_id=feedback_data.submission_id,
            source_type=feedback_data.source_type,
            feedback_text=feedback_data.feedback_text,
            triggers_rerun=feedback_data.triggers_rerun,
            rerun_scope=feedback_data.rerun_scope,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)

        logger.info(
            "Feedback recorded id=%s triggers_rerun=%s scope=%s",
            entry.id,
            entry.triggers_rerun,
            entry.rerun_scope,
        )

        if entry.triggers_rerun and entry.rerun_scope:
            await self._execute_rerun(
                submission_id=feedback_data.submission_id,
                scope=entry.rerun_scope,
                db=db,
            )

        return entry

    async def _execute_rerun(
        self,
        submission_id: UUID,
        scope: str,
        db: AsyncSession,
    ) -> None:
        """
        Execute the appropriate rerun based on scope.

        Version history is preserved because new AgentRun and PhaseOutput
        records are created — nothing is overwritten.
        """
        submission_data = await self._load_submission_data(submission_id, db)
        if not submission_data:
            logger.error(
                "Cannot rerun: submission %s not found.", submission_id
            )
            return

        logger.info("Triggering rerun scope=%r for submission %s", scope, submission_id)

        if scope == "phase1":
            dossier = await self._pipeline.run(submission_id, submission_data, db)
            await self._hoster.finalise_phase1(submission_id, dossier, db)

        elif scope == "eval":
            from agents.eval_agent import EvalAgent
            agent = EvalAgent()
            await agent.run(submission_id, submission_data, db)
            logger.info("EVAL rerun complete for submission %s", submission_id)

        elif scope == "team":
            from agents.team_agent import TeamAgent
            agent = TeamAgent()
            await agent.run(submission_id, submission_data, db)
            logger.info("TEAM rerun complete for submission %s", submission_id)

        else:
            logger.warning("Unknown rerun scope %r — no action taken.", scope)

    async def _load_submission_data(
        self, submission_id: UUID, db: AsyncSession
    ) -> dict[str, Any] | None:
        """Fetch the raw submission fields needed by agents."""
        result = await db.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        sub = result.scalar_one_or_none()
        if not sub:
            return None

        return {
            "startup_name": sub.startup_name,
            "one_line_pitch": sub.one_line_pitch,
            "problem_statement": sub.problem_statement,
            "proposed_solution": sub.proposed_solution,
            "target_market": sub.target_market,
            "industry_vertical": sub.industry_vertical,
            "business_model": sub.business_model,
            "traction_summary": sub.traction_summary,
            "competitive_landscape": sub.competitive_landscape,
            "technical_status": sub.technical_status,
            "stage": sub.stage,
            "supporting_documents": sub.supporting_documents,
            "team_members": sub.team_members,
        }
