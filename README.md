# KI Agentic Qualification System

An agentic startup qualification platform for the Kaplan Innovation accelerator. Phase 1 runs two specialist AI agents in parallel against each founder submission, producing a **Final Qualification Dossier** for human mentor review.

> No startup is autonomously approved or rejected. All AI outputs are advisory only.

---

## Architecture

```
Founder submits → POST /api/submissions
                      ↓
              POST /api/phase1/run/{id}
                      ↓
          ┌─────── asyncio.gather ────────┐
          │                               │
       EVAL Agent                    TEAM Agent
   (VC seed analyst)           (Org psychologist)
          │                               │
          └────────── merge ──────────────┘
                      ↓
            Final Qualification Dossier
            (PhaseOutput in PostgreSQL)
                      ↓
              Human Mentor Review
```

### Agents

| Agent | Persona | Output |
|-------|---------|--------|
| **EVAL** | Rigorous VC seed-stage analyst | Market, feasibility & scalability scores; red flags |
| **TEAM** | Organizational psychologist | Role alignment matrix; founder-market fit; gaps |

### Conflict Detection

If the EVAL and TEAM assessments diverge significantly, `mentor_review_required` is set to `true`:

- **Rule A**: `eval_avg >= 8` AND `founder_market_fit_score <= 4`
- **Rule B**: `eval_avg <= 4` AND `founder_market_fit_score >= 8`

---

## Project Structure

```
ki-agentic-system/
  agents/              # EVAL and TEAM agent implementations
  orchestrator/        # Phase 1 pipeline, hoster, feedback loop
  api/                 # FastAPI app, routes, deps
  models/              # SQLAlchemy async ORM models
  schemas/             # Pydantic v2 schemas
  services/            # Claude client, prompt loader, dossier builder
  prompts/             # System prompt .txt files
  tests/               # pytest test suite + JSON fixtures
  alembic/             # Database migrations
  frontend/            # Next.js 15 App Router frontend
```

---

## Prerequisites

- Python 3.11+
- Node.js 20+ and pnpm
- Docker and Docker Compose
- An Anthropic API key

---

## Quick Start (Docker Compose)

```bash
# 1. Clone and enter directory
cd ki-agentic-system

# 2. Create your .env file
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Start all services
docker compose up --build

# Services:
#   PostgreSQL  → localhost:5432
#   Backend API → http://localhost:8000
#   Frontend    → http://localhost:3000
#   API docs    → http://localhost:8000/docs
```

---

## Local Development (without Docker)

### Backend

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your DATABASE_URL and ANTHROPIC_API_KEY

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Set the backend URL
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local

# Start the dev server
pnpm dev
# Frontend → http://localhost:3000
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL async URL (`postgresql+asyncpg://...`) |
| `ANTHROPIC_API_KEY` | Yes | — | Your Anthropic API key |
| `CLAUDE_EVAL_MODEL` | No | `claude-sonnet-4-6` | Model used by the EVAL agent |
| `CLAUDE_TEAM_MODEL` | No | `claude-sonnet-4-6` | Model used by the TEAM agent |
| `NEXT_PUBLIC_API_BASE_URL` | Yes (frontend) | `http://localhost:8000` | Backend base URL for the frontend |
| `FRONTEND_ORIGIN` | No | `http://localhost:3000` | CORS allowed origin |

---

## Database Migrations

```bash
# Apply all migrations (run after first setup or after pulling new migrations)
alembic upgrade head

# Create a new migration after changing ORM models
alembic revision --autogenerate -m "describe your change"

# Roll back one migration
alembic downgrade -1

# Check current revision
alembic current
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/health/db` | DB readiness probe |
| `POST` | `/api/submissions` | Create a submission |
| `GET` | `/api/submissions` | List submissions |
| `GET` | `/api/submissions/{id}` | Get a submission |
| `POST` | `/api/phase1/run/{id}` | Trigger Phase 1 pipeline |
| `GET` | `/api/dossier/{id}` | Fetch the latest dossier |
| `POST` | `/api/feedback` | Submit mentor feedback |
| `GET` | `/api/agent-runs/{id}` | List agent run history |

Interactive docs: `http://localhost:8000/docs`

---

## Running Tests

```bash
# From the project root (with venv active)
pytest

# With verbose output
pytest -v

# Run a specific test file
pytest tests/test_eval_agent.py -v

# Run a specific test
pytest tests/test_phase1_pipeline.py::test_mentor_review_rule_a_high_eval_low_team -v
```

All tests mock the Claude API. No real API calls are made during testing.

### Test Fixtures

| Fixture | Expected Behaviour |
|---------|-------------------|
| `solo_researcher.json` | Surfaces commercialisation/team gap concerns; solo founder risk |
| `student_app.json` | Flags scalability concerns; campus market fragmentation |
| `medtech_spinout.json` | High viability scores; strong domain expertise recognised |

---

## Adding a New Agent (Phase 2+)

1. Create `agents/your_agent.py` subclassing `BaseAgent`
2. Implement `_build_prompt_context()`
3. Add a prompt file `prompts/your_agent_system_prompt.txt`
4. Add a Pydantic schema in `schemas/your_agent.py`
5. Wire it into `orchestrator/pipeline.py`
6. Add the model env var to `.env.example`

---

## Design Decisions

- **Async throughout**: SQLAlchemy 2.x async + asyncio for parallel agent execution
- **JSONB for agent outputs**: Flexible schema for evolving LLM output shapes
- **UUID primary keys**: Globally unique, safe to expose in URLs
- **Prompt files**: System prompts live in `prompts/*.txt`, versioned by SHA-256 hash, never hardcoded
- **No auto-approve/reject**: The system only produces recommendations; human mentors make all decisions
- **Coherence scoring**: Independent of LLM quality — measures structural validity of the output
- **Version history**: Agent runs are append-only; reruns create new records, preserving full audit trail

---

## Licence

Internal Kaplan Innovation use only.
