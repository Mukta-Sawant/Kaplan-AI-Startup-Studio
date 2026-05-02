"""
Phase 1 orchestration routes.

POST /api/submit                     — create submission + run Phase 1 in one call
POST /api/phase1/run/{submission_id} — trigger Phase 1 for an existing submission
GET  /api/dossier/{submission_id}    — fetch the latest qualification dossier
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, get_hoster, get_pipeline
from models.submission import Submission
from orchestrator.hoster import Hoster
from orchestrator.pipeline import Phase1Pipeline
from schemas.submission import SubmissionCreate

router = APIRouter(tags=["phase1"])


@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit_and_evaluate(
    payload: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    pipeline: Phase1Pipeline = Depends(get_pipeline),
    hoster: Hoster = Depends(get_hoster),
) -> dict:
    """
    Create a submission and immediately run Phase 1 evaluation.

    Combines POST /api/submissions + POST /api/phase1/run into a single call.
    Returns the dossier result along with the new submission ID.
    """
    team_members_data = [m.model_dump() for m in payload.team_members]
    sub = Submission(
        startup_name=payload.startup_name,
        one_line_pitch=payload.one_line_pitch,
        problem_statement=payload.problem_statement,
        proposed_solution=payload.proposed_solution,
        target_market=payload.target_market,
        industry_vertical=payload.industry_vertical,
        business_model=payload.business_model,
        traction_summary=payload.traction_summary,
        competitive_landscape=payload.competitive_landscape,
        technical_status=payload.technical_status,
        stage=payload.stage,
        supporting_documents=payload.supporting_documents,
        team_members=team_members_data,
        status="submitted",
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)

    submission_data = {
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

    try:
        dossier = await pipeline.run(sub.id, submission_data, db)
        phase_output = await hoster.finalise_phase1(sub.id, dossier, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Phase 1 pipeline failed: {exc}",
        ) from exc

    return {
        "message": "Submission created and Phase 1 complete.",
        "submission_id": str(sub.id),
        "phase_output_id": str(phase_output.id),
        "mentor_review_required": phase_output.mentor_review_required,
        "phase1_status": dossier.get("phase1_status", "complete"),
        "dossier": dossier,
    }


@router.post("/phase1/run/{submission_id}", status_code=status.HTTP_202_ACCEPTED)
async def run_phase1(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    pipeline: Phase1Pipeline = Depends(get_pipeline),
    hoster: Hoster = Depends(get_hoster),
) -> dict:
    """
    Trigger the Phase 1 evaluation pipeline for a submission.

    Runs EVAL and TEAM agents in parallel and persists the merged dossier.
    Returns the dossier summary immediately (synchronous for simplicity;
    background task queue can be added in Phase 2).
    """
    # Verify submission exists
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found.",
        )

    submission_data = {
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

    try:
        dossier = await pipeline.run(submission_id, submission_data, db)
        phase_output = await hoster.finalise_phase1(submission_id, dossier, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Phase 1 pipeline failed: {exc}",
        ) from exc

    return {
        "message": "Phase 1 complete.",
        "submission_id": str(submission_id),
        "phase_output_id": str(phase_output.id),
        "mentor_review_required": phase_output.mentor_review_required,
        "phase1_status": dossier.get("phase1_status", "complete"),
    }


@router.get("/dossier/{submission_id}")
async def get_dossier(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    hoster: Hoster = Depends(get_hoster),
) -> dict:
    """Fetch the most recent Phase 1 qualification dossier for a submission."""
    phase_output = await hoster.get_latest_dossier(
        submission_id, db, phase_name="phase1"
    )
    if not phase_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No dossier found for submission {submission_id}. Run Phase 1 first.",
        )
    return phase_output.merged_output
