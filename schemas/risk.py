"""
Pydantic v2 schemas for the RISK agent output contract.
"""

from typing import Optional
from pydantic import BaseModel, Field


class RiskItem(BaseModel):
    """A single identified risk entry."""

    risk_id: str
    category: str  # "market", "technical", "regulatory", "financial", "operational", "team"
    description: str
    probability: str  # "low", "medium", "high"
    impact: str  # "low", "medium", "high"
    mitigation_strategy: str
    residual_risk: str  # "low", "medium", "high"


class RiskAgentOutput(BaseModel):
    """Structured output produced by the RISK (Senior Risk Analyst) agent."""

    risk_register: list[RiskItem]
    overall_risk_score: int = Field(..., ge=1, le=10)
    critical_risks: list[str]
    market_risks: list[str]
    technical_risks: list[str]
    regulatory_risks: list[str]
    financial_risks: list[str]
    operational_risks: list[str]
    risk_mitigation_summary: str = Field(..., min_length=10)
    go_no_go_recommendation: str
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    clarification_request: Optional[str] = None
