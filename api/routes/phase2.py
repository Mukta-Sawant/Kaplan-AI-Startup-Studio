"""
Phase 2 orchestration routes.

POST /api/phase2/run/{submission_id}    — trigger Phase 2 for an existing submission
GET  /api/phase2/output/{submission_id} — fetch the latest Phase 2 analysis output
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, get_hoster, get_phase2_pipeline
from models.phase_output import PhaseOutput
from models.submission import Submission
from orchestrator.hoster import Hoster
from orchestrator.phase2_pipeline import Phase2Pipeline

router = APIRouter(tags=["phase2"])


@router.post("/phase2/run/{submission_id}", status_code=status.HTTP_202_ACCEPTED)
async def run_phase2(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    pipeline: Phase2Pipeline = Depends(get_phase2_pipeline),
    hoster: Hoster = Depends(get_hoster),
) -> dict:
    """
    Trigger the Phase 2 Stage One Analysis pipeline for a submission.

    Runs INTERACT, DISCOVERY, COMP, RISK, and GTM agents in parallel,
    then runs FIN with GTM context. Requires Phase 1 to be complete.

    Returns the merged Phase 2 analysis output immediately.
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

    # Fetch Phase 1 dossier to pass as upstream context
    phase1_output = await hoster.get_latest_dossier(submission_id, db, phase_name="phase1")
    if not phase1_output:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Phase 1 must be completed before running Phase 2 for submission {submission_id}. "
                "Run POST /api/phase1/run/{submission_id} first."
            ),
        )

    phase1_dossier = phase1_output.merged_output or {}

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
        phase2_output = await pipeline.run(
            submission_id, submission_data, db, phase1_dossier
        )
        phase_record = await hoster.finalise_phase2(submission_id, phase2_output, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Phase 2 pipeline failed: {exc}",
        ) from exc

    return {
        "message": "Phase 2 Stage One Analysis complete.",
        "submission_id": str(submission_id),
        "phase_output_id": str(phase_record.id),
        "phase2_status": phase2_output.get("phase2_status", "complete"),
        "agent_statuses": phase2_output.get("agent_statuses", {}),
    }


@router.get("/phase2/output/{submission_id}")
async def get_phase2_output(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Fetch the most recent Phase 2 analysis output for a submission.

    Returns the full merged output from all 6 Phase 2 agents:
    INTERACT, DISCOVERY, COMP, RISK, GTM, and FIN.
    """
    result = await db.execute(
        select(PhaseOutput)
        .where(
            PhaseOutput.submission_id == submission_id,
            PhaseOutput.phase_name == "phase2",
        )
        .order_by(PhaseOutput.created_at.desc())
        .limit(1)
    )
    phase_output = result.scalar_one_or_none()

    if not phase_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No Phase 2 output found for submission {submission_id}. "
                "Run POST /api/phase2/run/{submission_id} first."
            ),
        )

    return phase_output.merged_output


@router.get("/phase2/summary/{submission_id}")
async def get_phase2_summary(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Fetch a lightweight summary of Phase 2 outputs for a submission.

    Returns key scores and summaries from each Phase 2 agent without
    the full detail (useful for dashboards and list views).
    """
    result = await db.execute(
        select(PhaseOutput)
        .where(
            PhaseOutput.submission_id == submission_id,
            PhaseOutput.phase_name == "phase2",
        )
        .order_by(PhaseOutput.created_at.desc())
        .limit(1)
    )
    phase_output = result.scalar_one_or_none()

    if not phase_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No Phase 2 output found for submission {submission_id}.",
        )

    output = phase_output.merged_output or {}
    discovery = output.get("discovery") or {}
    comp = output.get("comp") or {}
    risk = output.get("risk") or {}
    gtm = output.get("gtm") or {}
    fin = output.get("fin") or {}
    interact = output.get("interact") or {}

    return {
        "submission_id": str(submission_id),
        "phase2_status": output.get("phase2_status", "unknown"),
        "agent_statuses": output.get("agent_statuses", {}),
        "summary": {
            "interact": {
                "question_count": len(interact.get("clarification_questions", [])),
                "priority_topics": interact.get("priority_topics", []),
                "confidence_level": interact.get("confidence_level"),
            },
            "discovery": {
                "tam": discovery.get("total_addressable_market"),
                "market_growth_rate": discovery.get("market_growth_rate"),
                "industry_maturity": discovery.get("industry_maturity"),
                "confidence_level": discovery.get("confidence_level"),
                "summary": discovery.get("discovery_summary"),
            },
            "comp": {
                "overall_competitive_score": comp.get("overall_competitive_score"),
                "direct_competitor_count": len(comp.get("direct_competitors", [])),
                "confidence_level": comp.get("confidence_level"),
                "summary": comp.get("comp_summary"),
            },
            "risk": {
                "overall_risk_score": risk.get("overall_risk_score"),
                "risk_count": len(risk.get("risk_register", [])),
                "go_no_go": risk.get("go_no_go_recommendation"),
                "confidence_level": risk.get("confidence_level"),
                "summary": risk.get("risk_mitigation_summary"),
            },
            "gtm": {
                "pricing_model": gtm.get("pricing_model"),
                "primary_segments": gtm.get("primary_target_segments", []),
                "confidence_level": gtm.get("confidence_level"),
                "summary": gtm.get("gtm_summary"),
            },
            "fin": {
                "investment_readiness_score": fin.get("investment_readiness_score"),
                "funding_ask": fin.get("funding_ask"),
                "runway_months": fin.get("runway_months"),
                "confidence_level": fin.get("confidence_level"),
                "summary": fin.get("fin_summary"),
            },
        },
    }
