"""
Pydantic v2 schemas for startup submission request and response contracts.
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from schemas.common import UUIDModel


# ---------------------------------------------------------------------------
# Team member sub-schema
# ---------------------------------------------------------------------------


class TeamMemberInput(BaseModel):
    """A single team member's profile included in the submission."""

    name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., min_length=1, max_length=200)
    resume_text: str = Field(..., min_length=10)
    linkedin_url: str = Field(..., min_length=5, max_length=500)
    domain_expertise: Optional[str] = None
    startup_experience: Optional[str] = None
    commitment_level: Optional[str] = None


# ---------------------------------------------------------------------------
# Create / update schemas
# ---------------------------------------------------------------------------

StartupStage = Literal["idea", "prototype", "MVP", "pilot", "revenue"]
SubmissionStatus = Literal[
    "submitted", "clarification_needed", "phase1_complete", "mentor_review_required"
]


class SubmissionCreate(BaseModel):
    """Payload accepted when a founder creates a new submission."""

    startup_name: str = Field(..., min_length=1, max_length=255)
    one_line_pitch: str = Field(..., min_length=10, max_length=500)
    problem_statement: str = Field(..., min_length=20)
    proposed_solution: str = Field(..., min_length=20)
    target_market: str = Field(..., min_length=10)
    industry_vertical: str = Field(..., min_length=1, max_length=255)
    business_model: Optional[str] = None
    traction_summary: Optional[str] = None
    competitive_landscape: Optional[str] = None
    technical_status: Optional[str] = None
    stage: StartupStage
    supporting_documents: Optional[list[str]] = None
    team_members: list[TeamMemberInput] = Field(..., min_length=1)

    @model_validator(mode="after")
    def at_least_one_team_member(self) -> "SubmissionCreate":
        if not self.team_members:
            raise ValueError("At least one team member is required.")
        return self


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class SubmissionResponse(UUIDModel):
    """Full submission record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    startup_name: str
    one_line_pitch: str
    problem_statement: str
    proposed_solution: str
    target_market: str
    industry_vertical: str
    business_model: Optional[str]
    traction_summary: Optional[str]
    competitive_landscape: Optional[str]
    technical_status: Optional[str]
    stage: str
    supporting_documents: Optional[list[str]]
    team_members: list[dict]
    status: str
    updated_at: datetime


class SubmissionListItem(BaseModel):
    """Lightweight submission summary for listing endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_name: str
    one_line_pitch: str
    stage: str
    status: str
    created_at: datetime
