"""
Helpers for loading local environment variables in development.

The repository ships an `env` file at the project root rather than the more
common `.env`. We load both names so local commands like Alembic and Uvicorn
pick up the same settings without requiring users to export them manually.
"""

from pathlib import Path

from dotenv import load_dotenv


def load_project_env() -> None:
    """Load project-level env files if present."""
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env", override=False)
    load_dotenv(project_root / "env", override=False)
