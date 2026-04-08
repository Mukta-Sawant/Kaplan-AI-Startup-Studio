"""
Pydantic v2 schemas for the Final Qualification Dossier.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from schemas.eval import EvalAgentOutput
from schemas.team import TeamAgentOutput


class FinalDossier(BaseModel):
    """The merged Phase 1 qualification dossier presented to human mentors."""

    submission_id: UUID
    phase: str
    eval_report: EvalAgentOutput
    team_report: TeamAgentOutput
    mentor_review_required: bool
    dossier_summary: str
    created_at: datetime


class DossierResponse(BaseModel):
    """API response wrapper for the dossier endpoint."""

    submission_id: UUID
    phase: str
    eval_report: dict
    team_report: dict
    mentor_review_required: bool
    dossier_summary: str
    created_at: datetime
