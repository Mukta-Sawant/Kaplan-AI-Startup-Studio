"""
Utility for loading system prompts from the prompts/ directory.

Prompts are loaded once and cached in memory for the lifetime of the process.
A version hash is computed from the file contents so agent runs can reference
which prompt version produced a given output.
"""

import hashlib
import os
from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class PromptNotFoundError(FileNotFoundError):
    """Raised when a prompt file does not exist."""


@lru_cache(maxsize=None)
def load_prompt(filename: str) -> str:
    """
    Load a prompt file from the prompts/ directory.

    Args:
        filename: The filename including extension, e.g. "eval_system_prompt.txt".

    Returns:
        The full text content of the prompt.

    Raises:
        PromptNotFoundError: If the file does not exist.
    """
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise PromptNotFoundError(
            f"Prompt file not found: {path}. "
            f"Ensure prompts/{filename} exists."
        )
    return path.read_text(encoding="utf-8")


def prompt_version(filename: str) -> str:
    """
    Return a short SHA-256 hash of the prompt file contents.

    This is stored alongside agent run records so output can always be
    traced back to the exact prompt that generated it.
    """
    content = load_prompt(filename)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
