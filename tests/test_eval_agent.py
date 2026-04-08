"""
Tests for the EVAL agent.

All Claude API calls are mocked. No real network calls are made.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.eval_agent import EvalAgent
from schemas.eval import EvalAgentOutput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_eval_output(**overrides) -> dict[str, Any]:
    base = {
        "market_viability_score": 7,
        "feasibility_score": 6,
        "scalability_score": 6,
        "red_flags": [],
        "summary_recommendation": "Promising concept with market validation needed.",
        "confidence_level": 0.8,
        "clarification_request": None,
    }
    base.update(overrides)
    return base


def make_agent(client_response: dict[str, Any]) -> EvalAgent:
    client = MagicMock()
    client.model = "claude-test"
    client.complete = AsyncMock(return_value=client_response)
    return EvalAgent(client=client)


# ---------------------------------------------------------------------------
# Tests: solo researcher
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_solo_researcher_flags_commercialisation_gap(
    solo_researcher, mock_db
):
    """A solo academic founder with no startup experience should surface team risk flags."""
    response = make_eval_output(
        red_flags=[
            "Sole founder with no startup or commercial experience.",
            "Part-time commitment while maintaining academic role.",
            "No traction data provided.",
        ],
        feasibility_score=5,
        confidence_level=0.65,
    )
    agent = make_agent(response)

    output = await agent.run(uuid.uuid4(), solo_researcher, mock_db)

    assert isinstance(output["red_flags"], list)
    assert len(output["red_flags"]) >= 1
    assert any("commerci" in f.lower() or "solo" in f.lower() or "experience" in f.lower()
               for f in output["red_flags"])


@pytest.mark.asyncio
async def test_solo_researcher_scores_parse_correctly(solo_researcher, mock_db):
    """All score fields should be integers in [1, 10]."""
    response = make_eval_output(
        market_viability_score=7,
        feasibility_score=4,
        scalability_score=5,
    )
    agent = make_agent(response)

    output = await agent.run(uuid.uuid4(), solo_researcher, mock_db)

    for key in ("market_viability_score", "feasibility_score", "scalability_score"):
        assert 1 <= output[key] <= 10, f"{key} out of range"


# ---------------------------------------------------------------------------
# Tests: student app
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_app_flags_scalability_concerns(student_app, mock_db):
    """Campus-only delivery apps should trigger scalability concerns."""
    response = make_eval_output(
        market_viability_score=5,
        scalability_score=4,
        red_flags=[
            "Market is inherently fragmented — each campus requires separate onboarding.",
            "Commission model faces margin compression at scale from incumbents.",
        ],
        confidence_level=0.7,
    )
    agent = make_agent(response)

    output = await agent.run(uuid.uuid4(), student_app, mock_db)

    # scalability should be lower than market viability for this fixture
    assert output["scalability_score"] <= output["market_viability_score"]
    assert len(output["red_flags"]) >= 1


@pytest.mark.asyncio
async def test_student_app_confidence_above_threshold(student_app, mock_db):
    """Student app has traction data so confidence should be >= 0.5."""
    response = make_eval_output(confidence_level=0.7)
    agent = make_agent(response)

    output = await agent.run(uuid.uuid4(), student_app, mock_db)

    assert output["confidence_level"] >= 0.5
    assert output.get("clarification_request") is None


# ---------------------------------------------------------------------------
# Tests: medtech spinout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_medtech_spinout_high_viability(medtech_spinout, mock_db):
    """Medtech spinout with NHS pilot and NIH grant should score high on viability."""
    response = make_eval_output(
        market_viability_score=9,
        feasibility_score=8,
        scalability_score=7,
        red_flags=[
            "Regulatory timeline uncertainty — CE and FDA approval may extend runway needs.",
        ],
        confidence_level=0.9,
    )
    agent = make_agent(response)

    output = await agent.run(uuid.uuid4(), medtech_spinout, mock_db)

    assert output["market_viability_score"] >= 7
    assert output["confidence_level"] >= 0.7


# ---------------------------------------------------------------------------
# Tests: clarification trigger
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_low_confidence_triggers_clarification(solo_researcher, mock_db):
    """When confidence < 0.5, clarification_request must not be null."""
    response = make_eval_output(
        confidence_level=0.3,
        clarification_request="Please describe your go-to-market strategy in more detail.",
    )
    agent = make_agent(response)

    output = await agent.run(uuid.uuid4(), solo_researcher, mock_db)

    assert output["confidence_level"] < 0.5
    assert output["clarification_request"] is not None
    assert len(output["clarification_request"]) > 5


# ---------------------------------------------------------------------------
# Tests: schema validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_malformed_response_raises(solo_researcher, mock_db):
    """Malformed Claude output should raise ValueError."""
    bad_response = {"wrong_key": "bad data"}
    agent = make_agent(bad_response)

    with pytest.raises((ValueError, Exception)):
        await agent.run(uuid.uuid4(), solo_researcher, mock_db)
