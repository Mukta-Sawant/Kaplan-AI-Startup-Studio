"""
SQLAlchemy ORM model for merged phase outputs (qualification dossiers).
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Boolean, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from models.db import Base


class PhaseOutput(Base):
    """Stores the merged output from all agents in a given phase."""

    __tablename__ = "phase_outputs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase_name: Mapped[str] = mapped_column(String(100), nullable=False)
    merged_output: Mapped[dict] = mapped_column(JSONB, nullable=False)
    mentor_review_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
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
    submission: Mapped["Submission"] = relationship(  # noqa: F821
        "Submission", back_populates="phase_outputs"
    )

    def __repr__(self) -> str:
        return (
            f"<PhaseOutput id={self.id} phase={self.phase_name!r} "
            f"mentor_review={self.mentor_review_required}>"
        )
