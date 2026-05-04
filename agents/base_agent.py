"""
Abstract base class for all qualification agents.

Concrete agents subclass BaseAgent and implement _build_prompt_context()
to shape the user-facing prompt content. All infrastructure - model calling,
JSON parsing, coherence scoring, and run persistence - is handled here.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.agent_run import AgentRun
from services.claude_client import ClaudeClient, ClaudeClientError
from services.coherence import compute_coherence
from services.hashing import hash_input
from services.prompt_loader import load_prompt, prompt_version

logger = logging.getLogger(__name__)

AGENT_VERSION = "1.0.0"
MAX_ATTEMPTS = 3  # auto-retry only on schema/validation failures
JSON_RETRY_HINT = (
    "Your previous response was invalid or truncated JSON. "
    "Retry with the same schema, but use shorter strings, fewer words, "
    "and no markdown or code fences. Return exactly one complete JSON object."
)


class BaseAgent(ABC):
    """
    Abstract agent that wraps a model call with persistence, versioning,
    coherence scoring, and structured JSON output parsing.

    Subclasses must implement:
        - agent_name: str class attribute
        - prompt_filename: str class attribute
        - _build_prompt_context(submission_data, upstream_context) -> str
    """

    agent_name: str
    prompt_filename: str

    def __init__(self, client: ClaudeClient) -> None:
        self._client = client
        self._system_prompt = load_prompt(self.prompt_filename)
        self._prompt_ver = prompt_version(self.prompt_filename)

    async def run(
        self,
        submission_id: UUID,
        submission_data: dict[str, Any],
        db: AsyncSession,
        upstream_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Execute the full agent lifecycle for a submission.
        """
        input_payload = {
            "submission_id": str(submission_id),
            "data": submission_data,
        }
        input_hash = hash_input(input_payload)

        # Coerce None scalars to empty strings so prompt builders can safely
        # join nested values without type errors.
        submission_data = _sanitise(submission_data)

        logger.info("Agent %r sanitised data, building prompt...", self.agent_name)
        prompt_content = self._build_prompt_context(submission_data, upstream_context)
        logger.info(
            "Agent %r prompt built successfully (%d chars)",
            self.agent_name,
            len(prompt_content),
        )
        logger.info(
            "Agent %r starting run for submission %s",
            self.agent_name,
            submission_id,
        )

        output_json: Optional[dict[str, Any]] = None
        run_status = "success"
        coherence = 0.0
        retry_extra_context: Optional[str] = None

        try:
            for attempt in range(1, MAX_ATTEMPTS + 1):
                try:
                    raw_output = await self._call_model(
                        prompt_content,
                        extra_context=retry_extra_context,
                    )
                    output_json = self._parse_json_response(raw_output)
                    coherence = self._compute_coherence(output_json)
                    break
                except ClaudeClientError as exc:
                    if self._should_retry_client_error(exc) and attempt < MAX_ATTEMPTS:
                        retry_extra_context = JSON_RETRY_HINT
                        logger.warning(
                            "Agent %r JSON formatting attempt %d/%d failed: %s - retrying with stricter JSON hint.",
                            self.agent_name,
                            attempt,
                            MAX_ATTEMPTS,
                            exc,
                        )
                        continue
                    # The Bedrock client already does retry/backoff internally.
                    # Retrying the whole agent here only helps when the model
                    # returned malformed JSON, which is handled above.
                    raise
                except ValueError as exc:
                    if attempt < MAX_ATTEMPTS:
                        retry_extra_context = JSON_RETRY_HINT
                        logger.warning(
                            "Agent %r schema/validation attempt %d/%d failed: %s - retrying.",
                            self.agent_name,
                            attempt,
                            MAX_ATTEMPTS,
                            exc,
                        )
                    else:
                        raise
                except Exception:
                    raise

            confidence = output_json.get("confidence_level", 1.0)
            if confidence < 0.5:
                run_status = "clarification_needed"

        except Exception as exc:
            logger.error(
                "Agent %r failed for submission %s after %d attempts: %s",
                self.agent_name,
                submission_id,
                MAX_ATTEMPTS,
                exc,
                exc_info=True,
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
                confidence_level=output_json.get("confidence_level")
                if output_json
                else None,
                run_status=run_status,
                db=db,
            )

        logger.info(
            "Agent %r completed with status=%s coherence=%.2f",
            self.agent_name,
            run_status,
            coherence,
        )
        return output_json

    @abstractmethod
    def _build_prompt_context(
        self,
        submission_data: dict[str, Any],
        upstream_context: Optional[dict[str, Any]],
    ) -> str:
        """
        Format the submission data into a structured string for the model.
        """

    async def _call_model(
        self, user_content: str, extra_context: Optional[str] = None
    ) -> dict[str, Any]:
        """Delegate to the shared model client."""
        return await self._client.complete(
            system_prompt=self._system_prompt,
            user_content=user_content,
            extra_system_context=extra_context,
        )

    def _should_retry_client_error(self, exc: ClaudeClientError) -> bool:
        """Retry only when the model returned malformed structured output."""
        message = str(exc).lower()
        return (
            "malformed json" in message
            or "expected a json object" in message
        )

    def _parse_json_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        """
        Validate that the raw response dict has the expected structure.
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
        """Load a prompt by filename."""
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
    Recursively replace None values with empty strings.
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            result[key] = ""
        elif isinstance(value, dict):
            result[key] = _sanitise(value)
        elif isinstance(value, list):
            result[key] = [
                _sanitise(item) if isinstance(item, dict) else ("" if item is None else item)
                for item in value
            ]
        else:
            result[key] = value
    return result
