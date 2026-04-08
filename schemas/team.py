"""
Pydantic v2 schemas for the TEAM agent output contract.
"""

from pydantic import BaseModel, Field


class RoleAlignmentEntry(BaseModel):
    """Alignment assessment for a single team member."""

    member_name: str
    role: str
    strengths: list[str]
    coverage_areas: list[str]
    gaps: list[str]


class TeamAgentOutput(BaseModel):
    """Structured output produced by the TEAM (organizational psychologist) agent."""

    role_alignment_matrix: list[RoleAlignmentEntry]
    founder_market_fit_score: int = Field(..., ge=1, le=10)
    identified_gaps: list[str]
    recommended_mentors: list[str]
    team_risk_factors: list[str]
    confidence_level: float = Field(..., ge=0.0, le=1.0)
