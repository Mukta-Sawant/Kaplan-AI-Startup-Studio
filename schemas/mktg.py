"""Pydantic v2 schemas for the MKTG agent output contract."""

from typing import Optional
from pydantic import BaseModel, Field


class ChannelTactic(BaseModel):
    channel: str
    tactic: str
    target_segment: str
    estimated_cost: str
    expected_reach: str
    priority: int


class ContentWeek(BaseModel):
    week: int
    theme: str
    content_type: str
    channel: str
    call_to_action: str


class MessagingTemplate(BaseModel):
    template_name: str
    channel: str
    subject_or_opener: str
    body: str
    call_to_action: str


class KPITarget(BaseModel):
    metric: str
    target_value: str
    measurement_method: str
    timeframe: str


class MktgAgentOutput(BaseModel):
    marketing_plan: list[ChannelTactic]
    content_calendar: list[ContentWeek]
    messaging_templates: list[MessagingTemplate]
    kpi_targets: list[KPITarget]
    mktg_summary: str = Field(..., min_length=10)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    clarification_request: Optional[str] = None
