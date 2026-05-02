"""
Pydantic v2 schemas for the INTERACT agent output contract.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ClarificationQuestion(BaseModel):
    """A single targeted clarification question."""

    question: str
    rationale: str
    topic_area: str
    priority: int = Field(..., ge=1, le=5)


class InteractAgentOutput(BaseModel):
    """Structured output produced by the INTERACT (VC Research Analyst) agent."""

    clarification_questions: list[ClarificationQuestion]
    priority_topics: list[str]
    information_gaps: list[str]
    recommended_follow_up_areas: list[str]
    interaction_summary: str = Field(..., min_length=10)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    clarification_request: Optional[str] = None
