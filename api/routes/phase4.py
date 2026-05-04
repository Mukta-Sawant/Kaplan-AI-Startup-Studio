"""
Phase 4 orchestration routes — Moving to Funding.

POST /api/phase4/run/{submission_id}    — trigger Phase 4 for a submission
GET  /api/phase4/output/{submission_id} — fetch the latest Phase 4 output
GET  /api/phase4/summary/{submission_id} — fetch a lightweight summary
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, get_hoster, get_phase4_pipeline
from models.phase_output import PhaseOutput
from models.submission import Submission
from orchestrator.hoster import Hoster
from orchestrator.phase4_pipeline import Phase4Pipeline

router = APIRouter(tags=["phase4"])


@router.post("/phase4/run/{submission_id}", status_code=status.HTTP_202_ACCEPTED)
async def run_phase4(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    pipeline: Phase4Pipeline = Depends(get_phase4_pipeline),
    hoster: Hoster = Depends(get_hoster),
) -> dict:
    """
    Trigger Phase 4 Moving to Funding pipeline for a submission.

    Runs DECKS (with optional data-gap re-run), then VC sequentially.
    Requires Phase 3 to be complete.
    """
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found.",
        )

    # Fetch Phase 1 dossier
    phase1_output = await hoster.get_latest_dossier(submission_id, db, phase_name="phase1")
    if not phase1_output:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Phase 1 must be completed before running Phase 4 for submission {submission_id}.",
        )

    # Fetch Phase 2 output
    phase2_record = await hoster.get_latest_dossier(submission_id, db, phase_name="phase2")
    if not phase2_record:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Phase 2 must be completed before running Phase 4 for submission {submission_id}. "
                "Run POST /api/phase2/run/{submission_id} first."
            ),
        )

    # Fetch Phase 3 output
    phase3_record = await hoster.get_latest_dossier(submission_id, db, phase_name="phase3")
    if not phase3_record:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Phase 3 must be completed before running Phase 4 for submission {submission_id}. "
                "Run POST /api/phase3/run/{submission_id} first."
            ),
        )

    phase1_dossier = phase1_output.merged_output or {}
    phase2_output = phase2_record.merged_output or {}
    phase3_output = phase3_record.merged_output or {}

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
        phase4_output = await pipeline.run(
            submission_id, submission_data, db,
            phase1_dossier, phase2_output, phase3_output,
        )
        phase_record = await hoster.finalise_phase4(submission_id, phase4_output, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Phase 4 pipeline failed: {exc}",
        ) from exc

    return {
        "message": "Phase 4 Moving to Funding complete.",
        "submission_id": str(submission_id),
        "phase_output_id": str(phase_record.id),
        "phase4_status": phase4_output.get("phase4_status", "complete"),
        "agent_statuses": phase4_output.get("agent_statuses", {}),
        "has_retriggered_data_gap": phase4_output.get("has_retriggered_data_gap", False),
        "mentor_consultation_required": phase4_output.get("mentor_consultation_required", False),
    }


@router.get("/phase4/output/{submission_id}")
async def get_phase4_output(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Fetch the most recent Phase 4 output for a submission.

    Returns the full merged output from DECKS and VC agents.
    """
    result = await db.execute(
        select(PhaseOutput)
        .where(
            PhaseOutput.submission_id == submission_id,
            PhaseOutput.phase_name == "phase4",
        )
        .order_by(PhaseOutput.created_at.desc())
        .limit(1)
    )
    phase_output = result.scalar_one_or_none()

    if not phase_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No Phase 4 output found for submission {submission_id}. "
                "Run POST /api/phase4/run/{submission_id} first."
            ),
        )

    return phase_output.merged_output


@router.get("/phase4/summary/{submission_id}")
async def get_phase4_summary(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Fetch a lightweight summary of Phase 4 outputs for a submission.
    """
    result = await db.execute(
        select(PhaseOutput)
        .where(
            PhaseOutput.submission_id == submission_id,
            PhaseOutput.phase_name == "phase4",
        )
        .order_by(PhaseOutput.created_at.desc())
        .limit(1)
    )
    phase_output = result.scalar_one_or_none()

    if not phase_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No Phase 4 output found for submission {submission_id}.",
        )

    output = phase_output.merged_output or {}
    decks = output.get("decks") or {}
    vc = output.get("vc") or {}
    scorecard = vc.get("fundability_scorecard") or {}

    return {
        "submission_id": str(submission_id),
        "phase4_status": output.get("phase4_status", "unknown"),
        "agent_statuses": output.get("agent_statuses", {}),
        "has_retriggered_data_gap": output.get("has_retriggered_data_gap", False),
        "mentor_consultation_required": output.get("mentor_consultation_required", False),
        "summary": {
            "decks": {
                "slide_count": len(decks.get("slide_outline", [])),
                "deck_readiness_score": decks.get("deck_readiness_score"),
                "critical_gap_count": sum(
                    1 for g in decks.get("data_gaps_identified", [])
                    if isinstance(g, dict) and g.get("severity") == "critical"
                ),
                "narrative_arc": decks.get("narrative_arc"),
                "confidence_level": decks.get("confidence_level"),
                "summary": decks.get("decks_summary"),
            },
            "vc": {
                "investor_count": len(vc.get("investor_list", [])),
                "fundability_overall_score": scorecard.get("overall_score"),
                "mentor_consultation_required": vc.get("mentor_consultation_required"),
                "confidence_level": vc.get("confidence_level"),
                "summary": vc.get("vc_summary"),
            },
        },
    }
