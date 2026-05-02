"""
SQLAlchemy ORM model for individual agent execution runs.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from models.db import Base


class AgentRun(Base):
    """Records a single execution of an AI agent, including inputs, outputs, and metadata."""

    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    system_prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    input_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    coherence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    run_status: Mapped[str] = mapped_column(
        SAEnum(
            "success",
            "failed",
            "clarification_needed",
            name="agent_run_status_enum",
        ),
        nullable=False,
        default="success",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    submission: Mapped["Submission"] = relationship(  # noqa: F821
        "Submission", back_populates="agent_runs"
    )

    def __repr__(self) -> str:
        return (
            f"<AgentRun id={self.id} agent={self.agent_name!r} "
            f"status={self.run_status} submission={self.submission_id}>"
        )
