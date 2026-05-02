"""
Pydantic v2 schemas for the FIN agent output contract.
"""

from typing import Optional
from pydantic import BaseModel, Field


class YearlyProjection(BaseModel):
    """Revenue and cost projections for a single fiscal year."""

    year: int
    revenue: str
    gross_margin: str
    operating_expenses: str
    ebitda: str
    headcount: int


class UnitEconomics(BaseModel):
    """Core unit economics metrics."""

    customer_acquisition_cost: str
    lifetime_value: str
    ltv_cac_ratio: str
    payback_period_months: int
    gross_margin_percent: str


class FinAgentOutput(BaseModel):
    """Structured output produced by the FIN (Early-Stage CFO) agent."""

    revenue_projections: list[YearlyProjection]
    burn_rate_monthly: str
    runway_months: int
    funding_ask: str
    pre_money_valuation: str
    use_of_funds: list[str]
    unit_economics: UnitEconomics
    key_financial_assumptions: list[str]
    financial_risk_factors: list[str]
    break_even_timeline: str
    investment_readiness_score: int = Field(..., ge=1, le=10)
    fin_summary: str = Field(..., min_length=10)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    clarification_request: Optional[str] = None
