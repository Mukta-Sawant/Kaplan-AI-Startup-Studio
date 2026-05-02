"""
Pydantic v2 schemas for the COMP agent output contract.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Competitor(BaseModel):
    """Assessment of a single competitor."""

    name: str
    type: str  # "direct" or "indirect"
    strengths: list[str]
    weaknesses: list[str]
    market_share_estimate: str
    threat_level: str  # "low", "medium", "high"


class CompAgentOutput(BaseModel):
    """Structured output produced by the COMP (Competitive Strategy Advisor) agent."""

    direct_competitors: list[Competitor]
    indirect_competitors: list[Competitor]
    competitive_advantages: list[str]
    competitive_disadvantages: list[str]
    differentiation_factors: list[str]
    moat_assessment: str = Field(..., min_length=10)
    competitive_positioning: str = Field(..., min_length=10)
    white_space_opportunities: list[str]
    competitive_risk_factors: list[str]
    overall_competitive_score: int = Field(..., ge=1, le=10)
    comp_summary: str = Field(..., min_length=10)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    clarification_request: Optional[str] = None
