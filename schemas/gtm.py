"""
Pydantic v2 schemas for the GTM agent output contract.
"""

from typing import Optional
from pydantic import BaseModel, Field


class MarketingChannel(BaseModel):
    """A single GTM channel with strategy details."""

    channel: str
    strategy: str
    estimated_cost: str
    expected_reach: str
    priority: int = Field(..., ge=1, le=5)


class GTMAgentOutput(BaseModel):
    """Structured output produced by the GTM (Seasoned Founder/CEO) agent."""

    primary_target_segments: list[str]
    ideal_customer_profile: str = Field(..., min_length=10)
    value_proposition: str = Field(..., min_length=10)
    pricing_model: str
    pricing_strategy: str = Field(..., min_length=10)
    marketing_channels: list[MarketingChannel]
    sales_strategy: str = Field(..., min_length=10)
    launch_timeline: str = Field(..., min_length=10)
    key_partnerships: list[str]
    customer_acquisition_strategy: str = Field(..., min_length=10)
    gtm_risk_factors: list[str]
    success_metrics: list[str]
    gtm_summary: str = Field(..., min_length=10)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    clarification_request: Optional[str] = None
