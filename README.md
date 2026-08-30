# KI Agentic Qualification System

An agentic startup qualification platform for the Kaplan Innovation accelerator. The system runs specialist AI agents across four sequential phases, from initial qualification through investor readiness, producing structured analysis for human mentor review at each stage.

> No startup is autonomously approved or rejected. All AI outputs are advisory only.

---

## Pipeline Overview

```
Founder submits
      ↓
  Phase 1: Initial Qualification
    EVAL Agent (VC analyst) ──┐
    TEAM Agent (Org psych)  ──┴── Final Qualification Dossier
      ↓
  Phase 2: Stage One Analysis
    INTERACT ─┐
    DISCOVERY ─┤
    COMP      ─┼── parallel ──→ FIN (sequential, needs GTM)
    RISK      ─┤
    GTM       ─┘
      ↓
  Phase 3: Stage Two Engagement
    CUST (with retry) → CHANNELS → MKTG   (sequential)
      ↓
  Phase 4: Moving to Funding
    DECKS (with optional data-gap re-run) → VC   (sequential)
      ↓
  Human Mentor Review
```

Each phase requires the previous to be complete. Outputs are persisted to PostgreSQL and accessible via the REST API and frontend dashboard.

---

## Agents

### Phase 1 — Initial Qualification

| Agent | Persona | Output |
|-------|---------|--------|
| **EVAL** | Rigorous VC seed-stage analyst | Market, feasibility & scalability scores; red flags; clarification requests |
| **TEAM** | Organizational psychologist | Role alignment matrix; founder-market fit score; team gaps |

Run in parallel via `asyncio.gather`. Conflict detection flags `mentor_review_required` when EVAL and TEAM scores diverge significantly.

### Phase 2 — Stage One Analysis

| Agent | Role | Key Outputs |
|-------|------|-------------|
| **INTERACT** | Clarification specialist | Priority questions, clarification requests |
| **DISCOVERY** | Market research analyst | TAM, market growth rate, industry maturity |
| **COMP** | Competitive intelligence | Direct/indirect competitors, competitive score |
| **RISK** | Risk assessment | Risk register, go/no-go recommendation |
| **GTM** | Go-to-market strategist | Pricing model, target segments, GTM plan |
| **FIN** | Financial analyst | Investment readiness score, funding ask, runway |

INTERACT, DISCOVERY, COMP, RISK, and GTM run in parallel. FIN runs sequentially after GTM with full GTM context.

### Phase 3 — Stage Two Engagement

| Agent | Role | Key Outputs |
|-------|------|-------------|
| **CUST** | Customer discovery | Customer segments, early adopter profile, outreach list |
| **CHANNELS** | Partnership mapper | Partner map, outreach priority ranking |
| **MKTG** | Marketing strategist | Marketing plan, messaging templates, KPI targets |

Agents run sequentially: CUST → CHANNELS → MKTG. CUST retries up to 3 times if confidence falls below 0.4. `mentor_intervention_required` is flagged when confidence remains low after retries.

### Phase 4 — Moving to Funding

| Agent | Role | Key Outputs |
|-------|------|-------------|
| **DECKS** | Pitch deck architect | 12-slide outline, data gaps, deck readiness score, narrative arc |
| **VC** | Investor matchmaker | Investor list, fundability scorecard, mentor consultation flag |

DECKS runs first and identifies critical data gaps. If a gap is found, the missing Phase 2 agent is re-run once and DECKS is re-run with updated context. VC runs after DECKS in a background task, allowing the API to respond immediately with DECKS results.

---

## Conflict Detection (Phase 1)

`mentor_review_required` is set to `true` when:

- **Rule A**: `eval_avg >= 8` AND `founder_market_fit_score <= 4`
- **Rule B**: `eval_avg <= 4` AND `founder_market_fit_score >= 8`

---

## Project Structure

```
ki-agentic-system/
  agents/              # All 13 agent implementations + BaseAgent
  orchestrator/        # Phase 1–4 pipelines, Hoster, feedback loop
  api/                 # FastAPI app, routes, dependency injection
  models/              # SQLAlchemy async ORM models (Submission, AgentRun, PhaseOutput, FeedbackEntry)
  schemas/             # Pydantic v2 schemas for all agents
  services/            # Claude client, prompt loader, dossier builder, hashing
  prompts/             # System prompt .txt files (versioned by SHA-256)
  tests/               # pytest test suite + JSON fixtures
  alembic/             # Database migrations
  frontend/            # Next.js 15 App Router frontend
    app/
      dashboard/       # Submissions dashboard
      startup/[id]/    # Unified startup detail page (all phases)
      submit/          # Submission form with resume upload
      phase2/[id]/     # Phase 2 analysis view
      phase3/[id]/     # Phase 3 engagement view
      phase4/[id]/     # Phase 4 funding view
      dossier/         # Phase 1 dossier view
    components/        # Shared React components
    lib/               # API client utilities
```

---

## Tech Stack

### Backend

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI 0.115 + Uvicorn |
| Async ORM | SQLAlchemy 2.x (async) |
| Database driver | asyncpg (PostgreSQL), aiosqlite (SQLite for tests) |
| Migrations | Alembic |
| Validation | Pydantic v2 + pydantic-settings |
| AI / LLM | Anthropic Claude (`claude-sonnet-4-6` by default) |
| PDF parsing | pypdf |
| Testing | pytest + pytest-asyncio + HTTPX |

### Frontend

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript 5 |
| UI | React 19 |
| Styling | Tailwind CSS 3 |
| Schema validation | Zod |
| E2E testing | Playwright |

### Infrastructure

| Component | Technology |
|-----------|-----------|
| Database | PostgreSQL |
| Containerisation | Docker + Docker Compose |
| API | REST (JSON) |

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
| `CLAUDE_EVAL_MODEL` | No | `claude-sonnet-4-6` | Model for the EVAL agent |
| `CLAUDE_TEAM_MODEL` | No | `claude-sonnet-4-6` | Model for the TEAM agent |
| `NEXT_PUBLIC_API_BASE_URL` | Yes (frontend) | `http://localhost:8000` | Backend base URL for the frontend |
| `FRONTEND_ORIGIN` | No | `http://localhost:3000` | CORS allowed origin |

---

## Database Migrations

```bash
# Apply all migrations
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

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/health/db` | DB readiness probe |

### Submissions

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/submissions` | Create a submission |
| `GET` | `/api/submissions` | List submissions |
| `GET` | `/api/submissions/{id}` | Get a submission |
| `GET` | `/api/agent-runs/{id}` | List agent run history |

### Phase 1 — Initial Qualification

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/phase1/run/{id}` | Trigger Phase 1 (EVAL + TEAM in parallel) |
| `GET` | `/api/dossier/{id}` | Fetch the Phase 1 dossier |

### Phase 2 — Stage One Analysis

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/phase2/run/{id}` | Trigger Phase 2 (6 agents) |
| `GET` | `/api/phase2/output/{id}` | Full Phase 2 output |
| `GET` | `/api/phase2/summary/{id}` | Lightweight summary (scores + highlights) |

### Phase 3 — Stage Two Engagement

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/phase3/run/{id}` | Trigger Phase 3 (CUST → CHANNELS → MKTG) |
| `GET` | `/api/phase3/output/{id}` | Full Phase 3 output |
| `GET` | `/api/phase3/summary/{id}` | Lightweight summary |

### Phase 4 — Moving to Funding

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/phase4/run/{id}` | Trigger Phase 4 (DECKS → VC in background) |
| `GET` | `/api/phase4/output/{id}` | Full Phase 4 output |
| `GET` | `/api/phase4/summary/{id}` | Lightweight summary (deck score, investor count) |

### Utilities

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/upload/resume` | Upload PDF or TXT resume; returns extracted text |
| `POST` | `/api/feedback` | Submit mentor feedback on a dossier |

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

## Adding a New Agent

1. Create `agents/your_agent.py` subclassing `BaseAgent`
2. Implement `_build_prompt_context()`
3. Add a prompt file `prompts/your_agent_system_prompt.txt`
4. Add a Pydantic schema in `schemas/your_agent.py`
5. Wire it into the relevant `orchestrator/phase*_pipeline.py`
6. Add the model env var to `.env.example`

---

## Design Decisions

- **Async throughout**: SQLAlchemy 2.x async + asyncio for parallel agent execution; each agent gets its own session to avoid concurrent transaction errors
- **Sequential phases with gates**: Each phase validates that the prior phase output exists before running, enforcing the qualification funnel
- **Partial failure handling**: If one agent in a parallel group fails, the pipeline uses a fallback output and sets `mentor_review_required` rather than aborting
- **CUST retry loop**: Phase 3's CUST agent retries up to 3× when confidence < 0.4, triggering `mentor_intervention_required` if it cannot reach threshold
- **DECKS data-gap re-run**: Phase 4 allows a single one-time re-run of a missing Phase 2 agent when DECKS identifies a critical data gap, then re-runs DECKS with updated context
- **Phase 4 background tasks**: The VC stage runs in a FastAPI `BackgroundTask` so the API responds immediately after DECKS completes; the VC output is persisted asynchronously
- **JSONB for agent outputs**: Flexible schema for evolving LLM output shapes without migrations
- **UUID primary keys**: Globally unique, safe to expose in URLs
- **Prompt files**: System prompts live in `prompts/*.txt`, versioned by SHA-256 hash, never hardcoded
- **No auto-approve/reject**: The system only produces recommendations; human mentors make all decisions
- **Version history**: Agent runs are append-only; reruns create new records, preserving a full audit trail
- **Resume upload**: PDF and plain-text resumes up to 5 MB can be uploaded and parsed server-side before submission

---
## Acknowledgments

This project was developed from the original concept and direction provided by Prof. Don DeLoach at the Kaplan Institute, Illinois Institute of Technology. I am grateful for his guidance and permission to publish this portfolio version. 

## Licence

Internal Kaplan Innovation use only.
