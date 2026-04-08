"""
Shared pytest fixtures for the KI Agentic System test suite.

All Claude API calls are mocked — no real network calls are made in tests.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixture data loaders
# ---------------------------------------------------------------------------

def load_fixture(filename: str) -> dict[str, Any]:
    """Load a JSON fixture file from tests/fixtures/."""
    path = FIXTURES_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def solo_researcher() -> dict[str, Any]:
    return load_fixture("solo_researcher.json")


@pytest.fixture
def student_app() -> dict[str, Any]:
    return load_fixture("student_app.json")


@pytest.fixture
def medtech_spinout() -> dict[str, Any]:
    return load_fixture("medtech_spinout.json")


# ---------------------------------------------------------------------------
# Claude API mock
# ---------------------------------------------------------------------------

EVAL_OUTPUT_TEMPLATE: dict[str, Any] = {
    "market_viability_score": 6,
    "feasibility_score": 5,
    "scalability_score": 5,
    "red_flags": [],
    "summary_recommendation": "The submission shows potential. Further validation is recommended.",
    "confidence_level": 0.75,
    "clarification_request": None,
}

TEAM_OUTPUT_TEMPLATE: dict[str, Any] = {
    "role_alignment_matrix": [
        {
            "member_name": "Test Founder",
            "role": "CEO",
            "strengths": ["domain knowledge"],
            "coverage_areas": ["product vision"],
            "gaps": ["go-to-market"],
        }
    ],
    "founder_market_fit_score": 6,
    "identified_gaps": [],
    "recommended_mentors": ["Sales & GTM mentor"],
    "team_risk_factors": [],
    "confidence_level": 0.75,
}


@pytest.fixture
def mock_eval_output() -> dict[str, Any]:
    return EVAL_OUTPUT_TEMPLATE.copy()


@pytest.fixture
def mock_team_output() -> dict[str, Any]:
    return TEAM_OUTPUT_TEMPLATE.copy()


@pytest.fixture
def mock_claude_client_factory():
    """
    Returns a factory that creates a mocked ClaudeClient.
    Call it with a response dict to preset what the client returns.
    """
    def factory(response: dict[str, Any]):
        client = MagicMock()
        client.model = "claude-sonnet-4-6-test"
        client.complete = AsyncMock(return_value=response)
        return client

    return factory


# ---------------------------------------------------------------------------
# DB mock
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    """A lightweight mock of an AsyncSession for unit tests."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db
