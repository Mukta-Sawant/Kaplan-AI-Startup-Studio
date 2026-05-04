"""Pydantic v2 schemas for the DECKS agent output contract."""

from typing import Optional
from pydantic import BaseModel, Field


class Slide(BaseModel):
    slide_number: int
    title: str
    key_points: list[str]
    speaker_notes: str
    visual_suggestion: str
    data_source_agents: list[str]


class DataGap(BaseModel):
    gap_description: str
    missing_from_agent: str
    severity: str  # "critical" | "moderate" | "minor"
    trigger_rerun: bool


class DecksAgentOutput(BaseModel):
    slide_outline: list[Slide]
    narrative_arc: str = Field(..., min_length=10)
    data_gaps_identified: list[DataGap]
    deck_readiness_score: int = Field(..., ge=1, le=10)
    decks_summary: str = Field(..., min_length=10)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    clarification_request: Optional[str] = None
