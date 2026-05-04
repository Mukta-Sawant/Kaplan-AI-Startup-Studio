"""
Phase 3 orchestration routes — Stage Two Engagement.

POST /api/phase3/run/{submission_id}    — trigger Phase 3 for a submission
GET  /api/phase3/output/{submission_id} — fetch the latest Phase 3 output
GET  /api/phase3/summary/{submission_id} — fetch a lightweight summary
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, get_hoster, get_phase3_pipeline
from models.phase_output import PhaseOutput
from models.submission import Submission
from orchestrator.hoster import Hoster
from orchestrator.phase3_pipeline import Phase3Pipeline

router = APIRouter(tags=["phase3"])


@router.post("/phase3/run/{submission_id}", status_code=status.HTTP_202_ACCEPTED)
async def run_phase3(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    pipeline: Phase3Pipeline = Depends(get_phase3_pipeline),
    hoster: Hoster = Depends(get_hoster),
) -> dict:
    """
    Trigger Phase 3 Stage Two Engagement pipeline for a submission.

    Runs CUST (with retry logic), then CHANNELS, then MKTG sequentially.
    Requires Phase 2 to be complete.
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
            detail=(
                f"Phase 1 must be completed before running Phase 3 for submission {submission_id}."
            ),
        )

    # Fetch Phase 2 output
    phase2_output_record = await hoster.get_latest_dossier(submission_id, db, phase_name="phase2")
    if not phase2_output_record:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Phase 2 must be completed before running Phase 3 for submission {submission_id}. "
                "Run POST /api/phase2/run/{submission_id} first."
            ),
        )

    phase1_dossier = phase1_output.merged_output or {}
    phase2_output = phase2_output_record.merged_output or {}

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
        phase3_output = await pipeline.run(
            submission_id, submission_data, db, phase1_dossier, phase2_output
        )
        phase_record = await hoster.finalise_phase3(submission_id, phase3_output, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Phase 3 pipeline failed: {exc}",
        ) from exc

    return {
        "message": "Phase 3 Stage Two Engagement complete.",
        "submission_id": str(submission_id),
        "phase_output_id": str(phase_record.id),
        "phase3_status": phase3_output.get("phase3_status", "complete"),
        "agent_statuses": phase3_output.get("agent_statuses", {}),
        "mentor_intervention_required": phase3_output.get("mentor_intervention_required", False),
        "cust_attempts": phase3_output.get("cust_attempts", 1),
    }


@router.get("/phase3/output/{submission_id}")
async def get_phase3_output(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Fetch the most recent Phase 3 output for a submission.

    Returns the full merged output from CUST, CHANNELS, and MKTG agents.
    """
    result = await db.execute(
        select(PhaseOutput)
        .where(
            PhaseOutput.submission_id == submission_id,
            PhaseOutput.phase_name == "phase3",
        )
        .order_by(PhaseOutput.created_at.desc())
        .limit(1)
    )
    phase_output = result.scalar_one_or_none()

    if not phase_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No Phase 3 output found for submission {submission_id}. "
                "Run POST /api/phase3/run/{submission_id} first."
            ),
        )

    return phase_output.merged_output


@router.get("/phase3/summary/{submission_id}")
async def get_phase3_summary(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Fetch a lightweight summary of Phase 3 outputs for a submission.
    """
    result = await db.execute(
        select(PhaseOutput)
        .where(
            PhaseOutput.submission_id == submission_id,
            PhaseOutput.phase_name == "phase3",
        )
        .order_by(PhaseOutput.created_at.desc())
        .limit(1)
    )
    phase_output = result.scalar_one_or_none()

    if not phase_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No Phase 3 output found for submission {submission_id}.",
        )

    output = phase_output.merged_output or {}
    cust = output.get("cust") or {}
    channels = output.get("channels") or {}
    mktg = output.get("mktg") or {}

    return {
        "submission_id": str(submission_id),
        "phase3_status": output.get("phase3_status", "unknown"),
        "agent_statuses": output.get("agent_statuses", {}),
        "mentor_intervention_required": output.get("mentor_intervention_required", False),
        "cust_attempts": output.get("cust_attempts", 1),
        "summary": {
            "cust": {
                "segment_count": len(cust.get("customer_segments", [])),
                "outreach_target_count": len(cust.get("outreach_list", [])),
                "early_adopter_profile": cust.get("early_adopter_profile"),
                "confidence_level": cust.get("confidence_level"),
                "summary": cust.get("cust_summary"),
            },
            "channels": {
                "partner_count": len(channels.get("partner_map", [])),
                "top_partners": channels.get("outreach_priority_ranking", [])[:5],
                "partnership_types": channels.get("partnership_types_breakdown", {}),
                "confidence_level": channels.get("confidence_level"),
                "summary": channels.get("channels_summary"),
            },
            "mktg": {
                "channel_count": len(mktg.get("marketing_plan", [])),
                "template_count": len(mktg.get("messaging_templates", [])),
                "kpi_count": len(mktg.get("kpi_targets", [])),
                "confidence_level": mktg.get("confidence_level"),
                "summary": mktg.get("mktg_summary"),
            },
        },
    }
