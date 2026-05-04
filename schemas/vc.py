"""Pydantic v2 schemas for the VC agent output contract."""

from typing import Optional
from pydantic import BaseModel, Field


class InvestorEntry(BaseModel):
    name: str
    investor_type: str
    fund_size: str
    stage_focus: str
    thesis_fit: str
    portfolio_examples: list[str]
    warm_intro_path: str
    geographic_focus: str
    priority_rank: int


class OutreachStrategy(BaseModel):
    recommended_sequence: list[str]
    pitch_customization_tips: list[str]
    timing_recommendation: str
    conference_opportunities: list[str]


class FundabilityScorecard(BaseModel):
    overall_score: int = Field(..., ge=1, le=10)
    team_score: int = Field(..., ge=1, le=10)
    market_score: int = Field(..., ge=1, le=10)
    traction_score: int = Field(..., ge=1, le=10)
    product_score: int = Field(..., ge=1, le=10)
    financial_score: int = Field(..., ge=1, le=10)
    score_breakdown: list[str]
    improvement_recommendations: list[str]


class VCAgentOutput(BaseModel):
    investor_list: list[InvestorEntry]
    outreach_strategy: OutreachStrategy
    fundability_scorecard: FundabilityScorecard
    mentor_consultation_required: bool
    vc_summary: str = Field(..., min_length=10)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    clarification_request: Optional[str] = None
