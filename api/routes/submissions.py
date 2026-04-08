"""
Submission CRUD routes.

POST /api/submissions     — create a new startup submission
GET  /api/submissions/{id} — fetch a submission by ID
GET  /api/agent-runs/{submission_id} — list all agent runs for a submission
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from models.agent_run import AgentRun
from models.submission import Submission
from schemas.submission import SubmissionCreate, SubmissionListItem, SubmissionResponse

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post(
    "",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_submission(
    payload: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    """Accept a new startup submission from a founder."""
    team_members_data = [
        m.model_dump() for m in payload.team_members
    ]

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
    return SubmissionResponse.model_validate(sub)


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    """Fetch a submission by its UUID."""
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found.",
        )
    return SubmissionResponse.model_validate(sub)


@router.get("", response_model=list[SubmissionListItem])
async def list_submissions(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
) -> list[SubmissionListItem]:
    """List all submissions (newest first)."""
    result = await db.execute(
        select(Submission)
        .order_by(Submission.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    subs = result.scalars().all()
    return [SubmissionListItem.model_validate(s) for s in subs]


# ---------------------------------------------------------------------------
# Agent runs sub-resource
# ---------------------------------------------------------------------------

agent_runs_router = APIRouter(prefix="/agent-runs", tags=["agent-runs"])


@agent_runs_router.get("/{submission_id}")
async def list_agent_runs(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all versioned agent runs for a submission, newest first."""
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.submission_id == submission_id)
        .order_by(AgentRun.created_at.desc())
    )
    runs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "agent_name": r.agent_name,
            "model_name": r.model_name,
            "version": r.version,
            "system_prompt_version": r.system_prompt_version,
            "run_status": r.run_status,
            "coherence_score": r.coherence_score,
            "confidence_level": r.confidence_level,
            "created_at": r.created_at.isoformat(),
        }
        for r in runs
    ]
