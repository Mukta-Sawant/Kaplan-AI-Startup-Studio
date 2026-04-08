"""
Pydantic v2 schemas for feedback submission and response.
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SourceType = Literal["founder", "mentor", "admin"]
RerunScope = Literal["eval", "team", "phase1"]


class FeedbackCreate(BaseModel):
    """Payload for submitting feedback on a qualification dossier."""

    submission_id: UUID
    source_type: SourceType
    feedback_text: str = Field(..., min_length=10)
    triggers_rerun: bool = False
    rerun_scope: Optional[RerunScope] = None


class FeedbackResponse(BaseModel):
    """Response returned after feedback is recorded."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    submission_id: UUID
    source_type: str
    feedback_text: str
    triggers_rerun: bool
    rerun_scope: Optional[str]
    created_at: datetime
