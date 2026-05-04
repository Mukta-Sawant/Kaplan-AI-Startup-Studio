"""Pydantic v2 schemas for the CHANNELS agent output contract."""

from typing import Optional
from pydantic import BaseModel, Field


class PartnerEntry(BaseModel):
    organization_name: str
    partnership_type: str
    shared_audience: str
    complementary_value: str
    is_competitor: bool
    outreach_priority: int


class ChannelsAgentOutput(BaseModel):
    partner_map: list[PartnerEntry]
    partnership_types_breakdown: dict
    outreach_priority_ranking: list[str]
    partnership_gaps: list[str]
    channels_summary: str = Field(..., min_length=10)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    clarification_request: Optional[str] = None
