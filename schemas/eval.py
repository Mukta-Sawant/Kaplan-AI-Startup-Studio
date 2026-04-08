"""
Pydantic v2 schemas for the EVAL agent output contract.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class EvalAgentOutput(BaseModel):
    """Structured output produced by the EVAL (VC analyst) agent."""

    market_viability_score: int = Field(..., ge=1, le=10)
    feasibility_score: int = Field(..., ge=1, le=10)
    scalability_score: int = Field(..., ge=1, le=10)
    red_flags: list[str]
    summary_recommendation: str = Field(..., min_length=10)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    clarification_request: Optional[str] = None

    @field_validator("red_flags")
    @classmethod
    def red_flags_must_be_strings(cls, v: list) -> list[str]:
        return [str(item) for item in v]

    @property
    def average_score(self) -> float:
        """Compute the mean of the three rubric scores."""
        return (
            self.market_viability_score
            + self.feasibility_score
            + self.scalability_score
        ) / 3.0
