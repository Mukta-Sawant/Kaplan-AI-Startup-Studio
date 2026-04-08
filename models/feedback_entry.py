"""
SQLAlchemy ORM model for mentor/founder feedback entries.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Boolean, Text, String, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from models.db import Base


class FeedbackEntry(Base):
    """Captures human feedback on a submission, optionally triggering agent reruns."""

    __tablename__ = "feedback_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(
        SAEnum("founder", "mentor", "admin", name="feedback_source_enum"),
        nullable=False,
    )
    feedback_text: Mapped[str] = mapped_column(Text, nullable=False)
    triggers_rerun: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rerun_scope: Mapped[Optional[str]] = mapped_column(
        SAEnum("eval", "team", "phase1", name="rerun_scope_enum"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    submission: Mapped["Submission"] = relationship(  # noqa: F821
        "Submission", back_populates="feedback_entries"
    )

    def __repr__(self) -> str:
        return (
            f"<FeedbackEntry id={self.id} source={self.source_type!r} "
            f"triggers_rerun={self.triggers_rerun}>"
        )
