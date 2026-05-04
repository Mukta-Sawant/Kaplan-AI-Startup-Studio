"""
AWS Bedrock client abstraction for Claude models.

Provides a single async interface for calling Claude via the Bedrock Runtime
Converse API. Uses httpx with direct Bearer-token authentication when
AWS_BEARER_TOKEN_BEDROCK is set (IAM Identity Center / Bedrock API tokens),
or falls back to boto3 SigV4 signing when standard AWS credentials are available.

Swap to a different provider by replacing this module only — the interface
(ClaudeClient, make_eval_client, make_team_client) stays the same.
"""

import asyncio
import json
import logging
import os
from typing import Any, Optional

import httpx
from services.env_loader import load_project_env

load_project_env()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MAX_TOKENS = 4096
PHASE3_MAX_TOKENS = 8192
PHASE4_MAX_TOKENS = 16384
DECKS_MAX_TOKENS = 8192
VC_MAX_TOKENS = 4096
DEFAULT_TIMEOUT_SECONDS = 180
PHASE4_TIMEOUT_SECONDS = 420
MAX_RETRIES = 3
PHASE4_MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 2.0  # seconds


class ClaudeClientError(Exception):
    """Raised when the Bedrock API returns an unrecoverable error."""


class ClaudeClient:
    """
    Async client for the AWS Bedrock Runtime Converse API.

    Uses Bearer-token auth (httpx) when AWS_BEARER_TOKEN_BEDROCK is set,
    which is the correct auth method for Bedrock API keys and IAM Identity
    Center tokens. Falls back to boto3 SigV4 when standard AWS credentials
    (AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY) are present instead.

    Usage::

        client = ClaudeClient(model="us.anthropic.claude-3-5-sonnet-20241022-v2:0")
        result = await client.complete(system_prompt="...", user_content="...")
    """

    def __init__(
        self,
        model: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.model = model or os.environ.get(
            "BEDROCK_MODEL_ID",
            "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        )
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries

        self._region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        self._bearer_token = os.environ.get("AWS_BEARER_TOKEN_BEDROCK")

        if not self._bearer_token:
            raise ClaudeClientError(
                "AWS_BEARER_TOKEN_BEDROCK is not set. "
                "Set it to your Bedrock API bearer token."
            )

        # Base URL for the Bedrock Runtime Converse API
        self._base_url = (
            f"https://bedrock-runtime.{self._region}.amazonaws.com"
        )

        logger.info(
            "ClaudeClient ready: model=%r region=%r base_url=%r",
            self.model,
            self._region,
            self._base_url,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def complete(
        self,
        system_prompt: str,
        user_content: str,
        extra_system_context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Send a system + user message pair and return the parsed JSON response.

        Args:
            system_prompt:        The agent's persona / instruction set.
            user_content:         The structured input data for this invocation.
            extra_system_context: Optional context appended to the system prompt.

        Returns:
            Parsed dict from the model's JSON response.

        Raises:
            ClaudeClientError: On API failure or malformed JSON after all retries.
        """
        full_system = system_prompt
        if extra_system_context:
            full_system = (
                f"{system_prompt}\n\n--- UPSTREAM CONTEXT ---\n{extra_system_context}"
            )

        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    "Bedrock Converse attempt %d/%d model=%s",
                    attempt, self.max_retries, self.model,
                )
                raw_text = await self._invoke(full_system, user_content)
                return self._parse_json(raw_text)

            except ClaudeClientError:
                raise  # non-retryable

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "Bedrock transport error on attempt %d/%d for model=%s "
                    "(%s: %r). Waiting %.1fs before retry.",
                    attempt,
                    self.max_retries,
                    self.model,
                    type(exc).__name__,
                    exc,
                    wait,
                )
                last_exc = exc
                await asyncio.sleep(wait)

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in (429, 503):
                    wait = RETRY_BACKOFF_BASE ** attempt
                    logger.warning(
                        "Bedrock throttled/unavailable (HTTP %d, attempt %d). Waiting %.1fs.",
                        status, attempt, wait,
                    )
                    last_exc = exc
                    await asyncio.sleep(wait)
                else:
                    body = exc.response.text
                    raise ClaudeClientError(
                        f"Bedrock HTTP {status}: {body[:400]}"
                    ) from exc

        raise ClaudeClientError(
            f"Bedrock call failed after {self.max_retries} attempts."
        ) from last_exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _invoke(self, system: str, user_content: str) -> str:
        """
        POST to the Bedrock Converse endpoint using Bearer-token auth.
        Returns the assistant's text response.
        """
        url = f"{self._base_url}/model/{self.model}/converse"
        payload = {
            "system": [{"text": system}],
            "messages": [
                {"role": "user", "content": [{"text": user_content}]}
            ],
            "inferenceConfig": {"maxTokens": self.max_tokens},
        }

        logger.info(
            "Bedrock POST %s | model=%s system_len=%d user_len=%d max_tokens=%d timeout=%.1fs",
            url,
            self.model,
            len(system),
            len(user_content),
            self.max_tokens,
            self.timeout,
        )

        timeout = httpx.Timeout(
            connect=min(self.timeout, 30.0),
            read=self.timeout,
            write=min(self.timeout, 60.0),
            pool=min(self.timeout, 30.0),
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._bearer_token}",
                    "Content-Type": "application/json",
                },
            )

        response.raise_for_status()
        data = response.json()

        # Converse response shape:
        # data["output"]["message"]["content"][0]["text"]
        try:
            return data["output"]["message"]["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ClaudeClientError(
                f"Unexpected Bedrock response shape: {json.dumps(data)[:400]}"
            ) from exc

    def _parse_json(self, raw_text: str) -> dict[str, Any]:
        """
        Extract and parse a JSON object from the model response text.
        Strips optional markdown code fences before parsing.
        """
        text = raw_text.strip()

        if text.startswith("```"):
            lines = text.splitlines()
            inner = (
                "\n".join(lines[1:-1])
                if lines[-1].startswith("```")
                else "\n".join(lines[1:])
            )
            text = inner.strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ClaudeClientError(
                f"Bedrock returned malformed JSON. "
                f"Raw content: {raw_text[:500]!r}"
            ) from exc

        if not isinstance(parsed, dict):
            raise ClaudeClientError(
                f"Expected a JSON object from Bedrock, got {type(parsed).__name__}."
            )

        return parsed


# ---------------------------------------------------------------------------
# Agent client factories
# ---------------------------------------------------------------------------

def make_eval_client() -> ClaudeClient:
    """Factory for the EVAL agent's Bedrock client."""
    model = os.environ.get("CLAUDE_EVAL_MODEL") or os.environ.get("BEDROCK_MODEL_ID")
    return ClaudeClient(model=model)


def make_team_client() -> ClaudeClient:
    """Factory for the TEAM agent's Bedrock client."""
    model = os.environ.get("CLAUDE_TEAM_MODEL") or os.environ.get("BEDROCK_MODEL_ID")
    return ClaudeClient(model=model)


def make_phase2_client() -> ClaudeClient:
    """Shared factory for all Phase 2 agents (INTERACT, DISCOVERY, COMP, RISK, GTM, FIN)."""
    model = os.environ.get("CLAUDE_PHASE2_MODEL") or os.environ.get("BEDROCK_MODEL_ID")
    return ClaudeClient(model=model)


def make_phase3_client() -> ClaudeClient:
    """Factory for Phase 3 agents (CUST, CHANNELS, MKTG) — needs larger output window."""
    model = os.environ.get("CLAUDE_PHASE3_MODEL") or os.environ.get("BEDROCK_MODEL_ID")
    return ClaudeClient(model=model, max_tokens=PHASE3_MAX_TOKENS)


def make_phase4_client() -> ClaudeClient:
    """Factory for Phase 4 agents (DECKS, VC) — needs larger output window."""
    model = os.environ.get("CLAUDE_PHASE4_MODEL") or os.environ.get("BEDROCK_MODEL_ID")
    timeout = float(
        os.environ.get("CLAUDE_PHASE4_TIMEOUT_SECONDS", PHASE4_TIMEOUT_SECONDS)
    )
    retries = int(os.environ.get("CLAUDE_PHASE4_MAX_RETRIES", PHASE4_MAX_RETRIES))
    return ClaudeClient(
        model=model,
        max_tokens=PHASE4_MAX_TOKENS,
        timeout=timeout,
        max_retries=retries,
    )


def make_decks_client() -> ClaudeClient:
    """Factory for the DECKS agent with a tighter token budget."""
    model = os.environ.get("CLAUDE_PHASE4_MODEL") or os.environ.get("BEDROCK_MODEL_ID")
    timeout = float(
        os.environ.get("CLAUDE_PHASE4_TIMEOUT_SECONDS", PHASE4_TIMEOUT_SECONDS)
    )
    max_tokens = int(os.environ.get("CLAUDE_DECKS_MAX_TOKENS", DECKS_MAX_TOKENS))
    retries = int(os.environ.get("CLAUDE_PHASE4_MAX_RETRIES", PHASE4_MAX_RETRIES))
    return ClaudeClient(
        model=model,
        max_tokens=max_tokens,
        timeout=timeout,
        max_retries=retries,
    )


def make_vc_client() -> ClaudeClient:
    """Factory for the VC agent with a tighter token budget."""
    model = os.environ.get("CLAUDE_PHASE4_MODEL") or os.environ.get("BEDROCK_MODEL_ID")
    timeout = float(
        os.environ.get("CLAUDE_PHASE4_TIMEOUT_SECONDS", PHASE4_TIMEOUT_SECONDS)
    )
    max_tokens = int(os.environ.get("CLAUDE_VC_MAX_TOKENS", VC_MAX_TOKENS))
    retries = int(os.environ.get("CLAUDE_PHASE4_MAX_RETRIES", PHASE4_MAX_RETRIES))
    return ClaudeClient(
        model=model,
        max_tokens=max_tokens,
        timeout=timeout,
        max_retries=retries,
    )
