"""
Integration tests for the Phase 1 orchestration pipeline.

All Claude API calls are mocked. No real network calls are made.
Database interactions are mocked to isolate orchestration logic.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.eval_agent import EvalAgent
from agents.team_agent import TeamAgent
from orchestrator.pipeline import Phase1Pipeline
from schemas.eval import EvalAgentOutput
from schemas.team import TeamAgentOutput
from services.dossier_builder import build_dossier, requires_mentor_review


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_eval_output(**overrides) -> dict[str, Any]:
    base = {
        "market_viability_score": 7,
        "feasibility_score": 6,
        "scalability_score": 6,
        "red_flags": [],
        "summary_recommendation": "Viable opportunity with execution risk.",
        "confidence_level": 0.8,
        "clarification_request": None,
    }
    base.update(overrides)
    return base


def make_team_output(**overrides) -> dict[str, Any]:
    base = {
        "role_alignment_matrix": [
            {
                "member_name": "Founder",
                "role": "CEO",
                "strengths": ["domain expertise"],
                "coverage_areas": ["product"],
                "gaps": ["sales"],
            }
        ],
        "founder_market_fit_score": 7,
        "identified_gaps": [],
        "recommended_mentors": ["GTM advisor"],
        "team_risk_factors": [],
        "confidence_level": 0.75,
    }
    base.update(overrides)
    return base


def make_pipeline(
    eval_response: dict[str, Any],
    team_response: dict[str, Any],
) -> Phase1Pipeline:
    eval_client = MagicMock()
    eval_client.model = "claude-eval-test"
    eval_client.complete = AsyncMock(return_value=eval_response)

    team_client = MagicMock()
    team_client.model = "claude-team-test"
    team_client.complete = AsyncMock(return_value=team_response)

    eval_agent = EvalAgent(client=eval_client)
    team_agent = TeamAgent(client=team_client)
    return Phase1Pipeline(eval_agent=eval_agent, team_agent=team_agent)


# ---------------------------------------------------------------------------
# Tests: parallel execution
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pipeline_returns_dossier_keys(student_app, mock_db):
    """Pipeline output must contain all required dossier keys."""
    pipeline = make_pipeline(make_eval_output(), make_team_output())

    dossier = await pipeline.run(uuid.uuid4(), student_app, mock_db)

    required_keys = {
        "submission_id", "phase", "eval_report", "team_report",
        "mentor_review_required", "dossier_summary", "created_at", "phase1_status",
    }
    assert required_keys.issubset(dossier.keys())


@pytest.mark.asyncio
async def test_pipeline_phase_is_phase1(medtech_spinout, mock_db):
    pipeline = make_pipeline(make_eval_output(), make_team_output())
    dossier = await pipeline.run(uuid.uuid4(), medtech_spinout, mock_db)
    assert dossier["phase"] == "phase1"


# ---------------------------------------------------------------------------
# Tests: clarification trigger
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_low_confidence_sets_clarification_status(solo_researcher, mock_db):
    """When EVAL confidence < 0.5, phase1_status must be 'clarification_needed'."""
    pipeline = make_pipeline(
        make_eval_output(
            confidence_level=0.3,
            clarification_request="Please clarify your go-to-market approach.",
        ),
        make_team_output(),
    )

    dossier = await pipeline.run(uuid.uuid4(), solo_researcher, mock_db)

    assert dossier["phase1_status"] == "clarification_needed"
    assert dossier.get("clarification_request") is not None


@pytest.mark.asyncio
async def test_high_confidence_sets_complete_status(student_app, mock_db):
    """When EVAL confidence >= 0.5, phase1_status must be 'complete'."""
    pipeline = make_pipeline(
        make_eval_output(confidence_level=0.8),
        make_team_output(),
    )

    dossier = await pipeline.run(uuid.uuid4(), student_app, mock_db)

    assert dossier["phase1_status"] == "complete"


# ---------------------------------------------------------------------------
# Tests: mentor review conflict detection
# ---------------------------------------------------------------------------

def test_mentor_review_rule_a_high_eval_low_team():
    """Rule A: strong eval + weak team -> mentor_review_required."""
    eval_out = EvalAgentOutput(
        market_viability_score=9,
        feasibility_score=8,
        scalability_score=9,
        red_flags=[],
        summary_recommendation="Strong market opportunity.",
        confidence_level=0.9,
        clarification_request=None,
    )
    team_out = TeamAgentOutput(
        role_alignment_matrix=[],
        founder_market_fit_score=3,
        identified_gaps=["No technical co-founder"],
        recommended_mentors=[],
        team_risk_factors=["Solo non-technical founder"],
        confidence_level=0.8,
    )
    assert requires_mentor_review(eval_out, team_out) is True


def test_mentor_review_rule_b_low_eval_high_team():
    """Rule B: weak eval + strong team -> mentor_review_required."""
    eval_out = EvalAgentOutput(
        market_viability_score=3,
        feasibility_score=4,
        scalability_score=3,
        red_flags=["No clear market", "Unvalidated assumptions"],
        summary_recommendation="Significant concerns about market viability.",
        confidence_level=0.8,
        clarification_request=None,
    )
    team_out = TeamAgentOutput(
        role_alignment_matrix=[],
        founder_market_fit_score=9,
        identified_gaps=[],
        recommended_mentors=[],
        team_risk_factors=[],
        confidence_level=0.85,
    )
    assert requires_mentor_review(eval_out, team_out) is True


def test_no_conflict_when_aligned():
    """No conflict when both eval and team are in similar ranges."""
    eval_out = EvalAgentOutput(
        market_viability_score=7,
        feasibility_score=6,
        scalability_score=7,
        red_flags=[],
        summary_recommendation="Good overall picture.",
        confidence_level=0.85,
        clarification_request=None,
    )
    team_out = TeamAgentOutput(
        role_alignment_matrix=[],
        founder_market_fit_score=7,
        identified_gaps=[],
        recommended_mentors=[],
        team_risk_factors=[],
        confidence_level=0.8,
    )
    assert requires_mentor_review(eval_out, team_out) is False


# ---------------------------------------------------------------------------
# Tests: partial failure handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_team_agent_failure_uses_fallback(solo_researcher, mock_db):
    """If TEAM agent fails, pipeline should complete with fallback values."""
    eval_client = MagicMock()
    eval_client.model = "claude-eval-test"
    eval_client.complete = AsyncMock(return_value=make_eval_output())

    team_client = MagicMock()
    team_client.model = "claude-team-test"
    team_client.complete = AsyncMock(side_effect=RuntimeError("Network error"))

    eval_agent = EvalAgent(client=eval_client)
    team_agent = TeamAgent(client=team_client)
    pipeline = Phase1Pipeline(eval_agent=eval_agent, team_agent=team_agent)

    # Should not raise — partial failure is handled gracefully
    dossier = await pipeline.run(uuid.uuid4(), solo_researcher, mock_db)
    assert "dossier_summary" in dossier
    assert dossier["mentor_review_required"] is True  # fallback triggers review
