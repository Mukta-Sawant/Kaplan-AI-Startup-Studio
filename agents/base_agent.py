"""
Abstract base class for all qualification agents.

Concrete agents (EvalAgent, TeamAgent) subclass BaseAgent and implement
_build_prompt_context() to shape the user-facing prompt content.
All infrastructure — model calling, JSON parsing, coherence scoring,
and run persistence — is handled here.
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.agent_run import AgentRun
from services.claude_client import ClaudeClient
from services.coherence import compute_coherence
from services.hashing import hash_input
from services.prompt_loader import load_prompt, prompt_version

logger = logging.getLogger(__name__)

AGENT_VERSION = "1.0.0"


class BaseAgent(ABC):
    """
    Abstract agent that wraps a Claude model call with persistence, versioning,
    coherence scoring, and structured JSON output parsing.

    Subclasses must implement:
        - agent_name: str class attribute
        - prompt_filename: str class attribute
        - _build_prompt_context(submission_data, upstream_context) -> str
    """

    agent_name: str  # e.g. "eval", "team"
    prompt_filename: str  # e.g. "eval_system_prompt.txt"

    def __init__(self, client: ClaudeClient) -> None:
        self._client = client
        self._system_prompt = load_prompt(self.prompt_filename)
        self._prompt_ver = prompt_version(self.prompt_filename)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run(
        self,
        submission_id: UUID,
        submission_data: dict[str, Any],
        db: AsyncSession,
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Execute the full agent lifecycle for a submission.

        Steps:
          1. Build structured user prompt content.
          2. Call the Claude model.
          3. Parse and validate the JSON response.
          4. Compute a coherence score.
          5. Persist the agent_run record.
          6. Return the typed output dict.

        Args:
            submission_id:   UUID of the parent submission.
            submission_data: Dict of submission fields relevant to this agent.
            db:              Active async SQLAlchemy session.
            upstream_context: Optional outputs from a prior agent pass.

        Returns:
            Parsed agent output dict.
        """
        input_payload = {
            "submission_id": str(submission_id),
            "data": submission_data,
        }
        input_hash = hash_input(input_payload)

        # Coerce any None scalar values to empty string so agent prompt
        # builders can safely call str.join() without a TypeError.
        submission_data = _sanitise(submission_data)

        logger.info("Agent %r sanitised data, building prompt...", self.agent_name)
        prompt_content = self._build_prompt_context(submission_data, upstream_context)
        logger.info("Agent %r prompt built successfully (%d chars)", self.agent_name, len(prompt_content))

        logger.info(
            "Agent %r starting run for submission %s", self.agent_name, submission_id
        )

        output_json: Optional[dict[str, Any]] = None
        run_status = "success"
        coherence = 0.0

        try:
            raw_output = await self._call_model(prompt_content)
            output_json = self._parse_json_response(raw_output)
            coherence = self._compute_coherence(output_json)

            # Determine run status from confidence level
            confidence = output_json.get("confidence_level", 1.0)
            if confidence < 0.5:
                run_status = "clarification_needed"

        except Exception as exc:
            logger.error(
                "Agent %r failed for submission %s: %s",
                self.agent_name, submission_id, exc,
                exc_info=True,  # prints full traceback
            )
            run_status = "failed"
            output_json = {"error": str(exc)}
            coherence = 0.0
            raise

        finally:
            await self._save_run(
                submission_id=submission_id,
                input_payload=input_payload,
                input_hash=input_hash,
                output_json=output_json or {},
                coherence_score=coherence,
                confidence_level=output_json.get("confidence_level") if output_json else None,
                run_status=run_status,
                db=db,
            )

        logger.info(
            "Agent %r completed with status=%s coherence=%.2f",
            self.agent_name, run_status, coherence,
        )
        return output_json

    # ------------------------------------------------------------------
    # Abstract — subclasses implement
    # ------------------------------------------------------------------

    @abstractmethod
    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]],
    ) -> str:
        """
        Format the submission data into a structured string to send as the
        user turn of the Claude request.
        """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _call_model(
        self, user_content: str, extra_context: Optional[str] = None
    ) -> dict[str, Any]:
        """Delegate to the Claude client."""
        return await self._client.complete(
            system_prompt=self._system_prompt,
            user_content=user_content,
            extra_system_context=extra_context,
        )

    def _parse_json_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        """
        Validate that the raw response dict has the expected structure.
        Raises ValueError on missing required top-level keys.
        """
        if not isinstance(raw, dict):
            raise ValueError(
                f"Agent {self.agent_name!r} expected a dict response, got {type(raw).__name__}."
            )
        return raw

    def _compute_coherence(self, output: dict[str, Any]) -> float:
        """Compute an agent-specific coherence score."""
        return compute_coherence(output, self.agent_name)

    def _load_prompt(self, filename: str) -> str:
        """Load a prompt by filename (convenience pass-through)."""
        return load_prompt(filename)

    async def _save_run(
        self,
        submission_id: UUID,
        input_payload: dict[str, Any],
        input_hash: str,
        output_json: dict[str, Any],
        coherence_score: float,
        confidence_level: Optional[float],
        run_status: str,
        db: AsyncSession,
    ) -> AgentRun:
        """Persist an AgentRun record to the database."""
        run = AgentRun(
            submission_id=submission_id,
            agent_name=self.agent_name,
            model_name=self._client.model,
            version=AGENT_VERSION,
            input_hash=input_hash,
            system_prompt_version=self._prompt_ver,
            input_payload=input_payload,
            output_json=output_json,
            coherence_score=coherence_score,
            confidence_level=confidence_level,
            run_status=run_status,
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        logger.debug("Saved AgentRun id=%s", run.id)
        return run


def _sanitise(data: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively replace None values with empty strings so prompt builders
    can safely call str.join() without a TypeError.
    Lists are walked element-by-element; nested dicts are sanitised too.
    """
    result: dict[str, Any] = {}
    for k, v in data.items():
        if v is None:
            result[k] = ""
        elif isinstance(v, dict):
            result[k] = _sanitise(v)
        elif isinstance(v, list):
            result[k] = [
                _sanitise(item) if isinstance(item, dict)
                else ("" if item is None else item)
                for item in v
            ]
        else:
            result[k] = v
    return result
