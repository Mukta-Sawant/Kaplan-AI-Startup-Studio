"""
SQLAlchemy ORM model for startup submissions.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from models.db import Base


class SubmissionStatus(str):
    SUBMITTED = "submitted"
    CLARIFICATION_NEEDED = "clarification_needed"
    PHASE1_COMPLETE = "phase1_complete"
    MENTOR_REVIEW_REQUIRED = "mentor_review_required"
    PHASE2_COMPLETE = "phase2_complete"


class Submission(Base):
    """Represents a startup submission by a founder."""

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    startup_name: Mapped[str] = mapped_column(String(255), nullable=False)
    one_line_pitch: Mapped[str] = mapped_column(String(500), nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_solution: Mapped[str] = mapped_column(Text, nullable=False)
    target_market: Mapped[str] = mapped_column(Text, nullable=False)
    industry_vertical: Mapped[str] = mapped_column(String(255), nullable=False)
    business_model: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    traction_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    competitive_landscape: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    technical_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stage: Mapped[str] = mapped_column(
        SAEnum(
            "idea", "prototype", "MVP", "pilot", "revenue",
            name="startup_stage_enum"
        ),
        nullable=False,
    )
    supporting_documents: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    team_members: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum(
            "submitted",
            "clarification_needed",
            "phase1_complete",
            "mentor_review_required",
            "phase2_complete",
            name="submission_status_enum",
        ),
        nullable=False,
        default="submitted",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    agent_runs: Mapped[list["AgentRun"]] = relationship(  # noqa: F821
        "AgentRun", back_populates="submission", cascade="all, delete-orphan"
    )
    phase_outputs: Mapped[list["PhaseOutput"]] = relationship(  # noqa: F821
        "PhaseOutput", back_populates="submission", cascade="all, delete-orphan"
    )
    feedback_entries: Mapped[list["FeedbackEntry"]] = relationship(  # noqa: F821
        "FeedbackEntry", back_populates="submission", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Submission id={self.id} name={self.startup_name!r} status={self.status}>"
