"""
FastAPI dependency injection helpers.

Provides async database sessions and shared service instances.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from models.db import AsyncSessionLocal
from orchestrator.feedback_loop import FeedbackLoop
from orchestrator.hoster import Hoster
from orchestrator.phase2_pipeline import Phase2Pipeline
from orchestrator.phase3_pipeline import Phase3Pipeline
from orchestrator.phase4_pipeline import Phase4Pipeline
from orchestrator.pipeline import Phase1Pipeline


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_pipeline() -> Phase1Pipeline:
    """Return a shared Phase1Pipeline instance."""
    return Phase1Pipeline()


def get_hoster() -> Hoster:
    """Return a shared Hoster instance."""
    return Hoster()


def get_phase2_pipeline() -> Phase2Pipeline:
    """Return a shared Phase2Pipeline instance."""
    return Phase2Pipeline()


def get_phase3_pipeline() -> Phase3Pipeline:
    """Return a shared Phase3Pipeline instance."""
    return Phase3Pipeline()


def get_phase4_pipeline() -> Phase4Pipeline:
    """Return a shared Phase4Pipeline instance."""
    return Phase4Pipeline()


def get_feedback_loop() -> FeedbackLoop:
    """Return a shared FeedbackLoop instance."""
    return FeedbackLoop()
