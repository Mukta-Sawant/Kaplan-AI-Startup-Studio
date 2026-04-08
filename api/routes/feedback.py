"""
Feedback routes.

POST /api/feedback — submit mentor/founder feedback, optionally trigger rerun
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, get_feedback_loop
from orchestrator.feedback_loop import FeedbackLoop
from schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    payload: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    feedback_loop: FeedbackLoop = Depends(get_feedback_loop),
) -> FeedbackResponse:
    """
    Record feedback from a mentor, founder, or admin.

    If triggers_rerun is true and rerun_scope is provided, the appropriate
    agents will be re-executed and a new dossier version will be created.
    """
    try:
        entry = await feedback_loop.process(payload, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback processing failed: {exc}",
        ) from exc

    return FeedbackResponse.model_validate(entry)
