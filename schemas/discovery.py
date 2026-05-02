"""
Pydantic v2 schemas for the DISCOVERY agent output contract.
"""

from typing import Optional
from pydantic import BaseModel, Field


class MarketSegment(BaseModel):
    """A distinct addressable market segment."""

    segment_name: str
    estimated_size: str
    growth_potential: str
    accessibility: str


class DiscoveryAgentOutput(BaseModel):
    """Structured output produced by the DISCOVERY (Industry Consultant) agent."""

    total_addressable_market: str
    serviceable_addressable_market: str
    serviceable_obtainable_market: str
    market_growth_rate: str
    key_market_trends: list[str]
    market_segments: list[MarketSegment]
    regulatory_landscape: str = Field(..., min_length=10)
    industry_maturity: str
    market_entry_barriers: list[str]
    market_opportunities: list[str]
    market_threats: list[str]
    discovery_summary: str = Field(..., min_length=10)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    clarification_request: Optional[str] = None
