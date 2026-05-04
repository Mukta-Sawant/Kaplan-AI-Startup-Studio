"""Pydantic v2 schemas for the CUST agent output contract."""

from typing import Optional
from pydantic import BaseModel, Field


class CustomerSegment(BaseModel):
    segment_name: str
    demographic_profile: str
    professional_profile: str
    pain_points: list[str]
    estimated_segment_size: str
    priority_rank: int


class OutreachTarget(BaseModel):
    target_type: str
    profile_description: str
    discovery_channel: str
    outreach_rationale: str


class CustAgentOutput(BaseModel):
    customer_segments: list[CustomerSegment]
    early_adopter_profile: str = Field(..., min_length=10)
    outreach_list: list[OutreachTarget]
    interview_script_suggestions: list[str]
    cust_summary: str = Field(..., min_length=10)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    clarification_request: Optional[str] = None
