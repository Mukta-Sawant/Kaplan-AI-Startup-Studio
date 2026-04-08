"""
Tests for the TEAM agent.

All Claude API calls are mocked. No real network calls are made.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.team_agent import TeamAgent
from schemas.team import TeamAgentOutput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_team_output(**overrides) -> dict[str, Any]:
    base = {
        "role_alignment_matrix": [
            {
                "member_name": "Test Founder",
                "role": "CEO",
                "strengths": ["domain expertise"],
                "coverage_areas": ["product vision"],
                "gaps": ["sales", "fundraising"],
            }
        ],
        "founder_market_fit_score": 7,
        "identified_gaps": [],
        "recommended_mentors": ["Sales & GTM mentor"],
        "team_risk_factors": [],
        "confidence_level": 0.75,
    }
    base.update(overrides)
    return base


def make_agent(client_response: dict[str, Any]) -> TeamAgent:
    client = MagicMock()
    client.model = "claude-test"
    client.complete = AsyncMock(return_value=client_response)
    return TeamAgent(client=client)


# ---------------------------------------------------------------------------
# Tests: solo researcher
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_solo_researcher_flags_missing_roles(solo_researcher, mock_db):
    """Solo academic founder should have identified gaps for business and sales roles."""
    response = make_team_output(
        role_alignment_matrix=[
            {
                "member_name": "Dr. Maya Osei",
                "role": "Founder & CEO",
                "strengths": ["deep domain research expertise", "academic publishing network"],
                "coverage_areas": ["product vision", "research validation"],
                "gaps": ["sales", "business development", "fundraising", "go-to-market strategy"],
            }
        ],
        founder_market_fit_score=7,
        identified_gaps=[
            "No business development or sales capability",
            "No go-to-market expertise",
            "No operational or finance lead",
        ],
        recommended_mentors=[
            "Deep tech commercialisation mentor",
            "University-to-industry licensing specialist",
            "Sales & business development advisor",
        ],
        team_risk_factors=[
            "Solo founder with no co-founder — key person risk",
            "Part-time commitment limits execution velocity",
        ],
        confidence_level=0.72,
    )
    agent = make_agent(response)

    output = await agent.run(uuid.uuid4(), solo_researcher, mock_db)

    gaps = output["identified_gaps"]
    assert len(gaps) >= 2
    assert any("sales" in g.lower() or "go-to-market" in g.lower() or "commerci" in g.lower()
               for g in gaps)


@pytest.mark.asyncio
async def test_solo_researcher_team_risk_flagged(solo_researcher, mock_db):
    """Solo founder should surface key person risk."""
    response = make_team_output(
        team_risk_factors=["Solo founder — single point of failure", "Part-time commitment"],
    )
    agent = make_agent(response)

    output = await agent.run(uuid.uuid4(), solo_researcher, mock_db)

    assert len(output["team_risk_factors"]) >= 1


# ---------------------------------------------------------------------------
# Tests: student app
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_app_two_members_in_matrix(student_app, mock_db):
    """Student app has two co-founders — both should appear in the matrix."""
    response = make_team_output(
        role_alignment_matrix=[
            {
                "member_name": "Jordan Kim",
                "role": "Co-Founder & CEO",
                "strengths": ["campus community knowledge", "peer-to-peer commerce"],
                "coverage_areas": ["operations", "partnerships"],
                "gaps": ["financial modelling", "investor relations"],
            },
            {
                "member_name": "Priya Sharma",
                "role": "Co-Founder & CTO",
                "strengths": ["mobile development", "Firebase"],
                "coverage_areas": ["product", "technology"],
                "gaps": ["system architecture at scale", "DevOps"],
            },
        ],
        founder_market_fit_score=6,
        identified_gaps=["No marketing or growth lead", "No finance lead"],
        confidence_level=0.7,
    )
    agent = make_agent(response)

    output = await agent.run(uuid.uuid4(), student_app, mock_db)

    assert len(output["role_alignment_matrix"]) == 2
    names = [e["member_name"] for e in output["role_alignment_matrix"]]
    assert "Jordan Kim" in names
    assert "Priya Sharma" in names


# ---------------------------------------------------------------------------
# Tests: medtech spinout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_medtech_spinout_high_fit_score(medtech_spinout, mock_db):
    """NeuroPatch has strong domain expertise — fit score should be >= 8."""
    response = make_team_output(
        founder_market_fit_score=9,
        identified_gaps=["Commercial/sales leadership needed for NHS procurement"],
        recommended_mentors=[
            "NHS procurement and reimbursement specialist",
            "MedTech Series A fundraising advisor",
        ],
        team_risk_factors=[
            "CMO is part-time — may create bottleneck during NHS expansion"
        ],
        confidence_level=0.88,
        role_alignment_matrix=[
            {
                "member_name": "Dr. Sarah Whitfield",
                "role": "Co-Founder & CEO",
                "strengths": ["clinical neurology expertise", "prior device commercialisation"],
                "coverage_areas": ["clinical strategy", "regulatory affairs", "investor relations"],
                "gaps": ["enterprise sales"],
            },
            {
                "member_name": "Amir Hassan",
                "role": "Co-Founder & CTO",
                "strengths": ["EEG signal processing", "CE marking experience", "FHIR integration"],
                "coverage_areas": ["device engineering", "regulatory software compliance"],
                "gaps": [],
            },
            {
                "member_name": "Dr. Priya Nair",
                "role": "Chief Medical Officer",
                "strengths": ["NHS primary care network", "clinical validation"],
                "coverage_areas": ["clinical affairs", "GP adoption strategy"],
                "gaps": ["limited time commitment"],
            },
        ],
    )
    agent = make_agent(response)

    output = await agent.run(uuid.uuid4(), medtech_spinout, mock_db)

    assert output["founder_market_fit_score"] >= 8
    assert len(output["role_alignment_matrix"]) == 3


@pytest.mark.asyncio
async def test_medtech_subject_matter_expertise_recognised(medtech_spinout, mock_db):
    """Deep domain expertise should appear in coverage_areas or strengths."""
    response = make_team_output(
        role_alignment_matrix=[
            {
                "member_name": "Dr. Sarah Whitfield",
                "role": "Co-Founder & CEO",
                "strengths": ["neurology expertise", "device licensing track record"],
                "coverage_areas": ["clinical strategy", "regulatory pathway"],
                "gaps": [],
            },
        ],
        founder_market_fit_score=9,
        confidence_level=0.9,
    )
    agent = make_agent(response)

    output = await agent.run(uuid.uuid4(), medtech_spinout, mock_db)

    all_strengths = [
        s
        for entry in output["role_alignment_matrix"]
        for s in entry.get("strengths", [])
    ]
    assert any("neuro" in s.lower() or "domain" in s.lower() or "expert" in s.lower()
               for s in all_strengths)


# ---------------------------------------------------------------------------
# Tests: schema validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_required_fields_raises(solo_researcher, mock_db):
    """A response missing required fields should fail schema validation."""
    bad_response = {"role_alignment_matrix": [], "founder_market_fit_score": 5}
    agent = make_agent(bad_response)

    with pytest.raises((ValueError, Exception)):
        await agent.run(uuid.uuid4(), solo_researcher, mock_db)
