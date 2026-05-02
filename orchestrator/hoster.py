"""
Submission lifecycle state manager (Hoster).

Manages transitions between submission statuses, persists phase outputs
(Final Qualification Dossiers), and determines mentor review requirements.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.phase_output import PhaseOutput
from models.submission import Submission

logger = logging.getLogger(__name__)


class Hoster:
    """
    Manages the lifecycle of a startup submission through the qualification pipeline.

    Responsibilities:
    - Transition submission status after phase completion.
    - Persist the merged dossier as a PhaseOutput record.
    - Apply conflict detection rules to set mentor_review_required.
    """

    async def finalise_phase1(
        self,
        submission_id: UUID,
        dossier: dict[str, Any],
        db: AsyncSession,
    ) -> PhaseOutput:
        """
        Persist the Phase 1 dossier and update the submission status accordingly.

        Args:
            submission_id: UUID of the submission.
            dossier:       The merged dossier dict from Phase1Pipeline.
            db:            Active async session.

        Returns:
            The persisted PhaseOutput record.
        """
        phase1_status = dossier.get("phase1_status", "complete")
        mentor_review = bool(dossier.get("mentor_review_required", False))

        # Persist the phase output
        phase_output = PhaseOutput(
            submission_id=submission_id,
            phase_name="phase1",
            merged_output=dossier,
            mentor_review_required=mentor_review,
        )
        db.add(phase_output)

        # Update submission status
        submission = await self._get_submission(submission_id, db)
        if submission:
            if phase1_status == "clarification_needed":
                submission.status = "clarification_needed"
            elif mentor_review:
                submission.status = "mentor_review_required"
            else:
                submission.status = "phase1_complete"

            logger.info(
                "Submission %s status -> %s (mentor_review=%s)",
                submission_id,
                submission.status,
                mentor_review,
            )

        await db.commit()
        await db.refresh(phase_output)
        return phase_output

    async def finalise_phase2(
        self,
        submission_id: UUID,
        phase2_output: dict[str, Any],
        db: AsyncSession,
    ) -> PhaseOutput:
        """
        Persist the Phase 2 output and update the submission status.

        Args:
            submission_id:  UUID of the submission.
            phase2_output:  The merged output dict from Phase2Pipeline.
            db:             Active async session.

        Returns:
            The persisted PhaseOutput record.
        """
        phase_record = PhaseOutput(
            submission_id=submission_id,
            phase_name="phase2",
            merged_output=phase2_output,
            mentor_review_required=False,
        )
        db.add(phase_record)

        submission = await self._get_submission(submission_id, db)
        if submission:
            submission.status = "phase2_complete"
            logger.info(
                "Submission %s status -> phase2_complete",
                submission_id,
            )

        await db.commit()
        await db.refresh(phase_record)
        return phase_record

    async def get_latest_dossier(
        self,
        submission_id: UUID,
        db: AsyncSession,
        phase_name: str | None = None,
    ) -> PhaseOutput | None:
        """Retrieve the most recent PhaseOutput for a submission.

        Args:
            submission_id: UUID of the submission.
            db:            Active async session.
            phase_name:    If provided, filter to this specific phase name.
        """
        query = (
            select(PhaseOutput)
            .where(PhaseOutput.submission_id == submission_id)
        )
        if phase_name:
            query = query.where(PhaseOutput.phase_name == phase_name)

        result = await db.execute(
            query.order_by(PhaseOutput.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_submission(
        self, submission_id: UUID, db: AsyncSession
    ) -> Submission | None:
        result = await db.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        return result.scalar_one_or_none()
