# Backend - Autonomous Support Resolution Engine

The backend is responsible for APIs, autonomous ticket processing, state management, and complete decision auditing.

## System Overview

Core backend capabilities:

- JWT-based authentication for dashboard/API access
- Ticket lifecycle management (pending, processing, resolved, escalated, failed)
- LangGraph-driven agent loop for autonomous decision making
- Policy-aware tool orchestration with mandatory guardrails
- Full audit trail capture at run, step, and tool-call levels
- Scheduler-based automatic polling of pending tickets

## Technology Stack

- Runtime: Python 3.12
- API framework: FastAPI + Uvicorn
- Data layer: SQLAlchemy (async), Alembic
- Primary database: PostgreSQL
- Cache/session/checkpoint: Redis
- Scheduler: APScheduler
- Agent orchestration: LangGraph + LangChain tool interfaces
- Knowledge retrieval: Chroma vector index + knowledge base service
- Security: JWT + Basic auth (for login/docs)
- Logging: structured log adapter with contextual metadata

## Backend Architecture

```text
HTTP API Layer (app/apis)
    -> Service Layer (app/services)
        -> Repository Layer (app/repositories)
            -> PostgreSQL

Agent Layer (app/agents)
    -> Prompt + Nodes + Edges + Tools
        -> LLM Provider
        -> Knowledge Base Search
        -> Action Tools (reply/refund/escalate)
    -> Audit Persistence (runs/steps/tool calls)
```

## Agent Workflow

1. Claim pending tickets (`claim_pending`) from PostgreSQL.
2. Create `agent_run` record for traceability.
3. Execute graph with controlled concurrency and retries.
4. Enforce guardrails:
   - policy-sensitive decisions require knowledge-base lookup
   - refund issuance requires eligibility check
5. Persist all step and tool details.
6. Finalize ticket and run outcome.

## API Surface

Base path: `/api/v1`

- Auth
  - `POST /auth/login`
- Tickets
  - `GET /tickets/`
  - `GET /tickets/{ticket_id}`
  - `GET /tickets/{ticket_id}/status`
  - `PATCH /tickets/{ticket_id}/status`
- Dashboard
  - `GET /dashboard/metrics`
  - `GET /dashboard/recent-activity`
- Audit
  - `GET /audit/{ticket_id}`

## Local Run (Without Docker)

### 1. Configure environment

```bash
cp .env.example .env
```

Update DB/Redis credentials and API keys in `.env`.

For Docker compose deployment, use:

```bash
cp .env.docker.example .env.docker
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run migrations

```bash
alembic upgrade head
```

### 4. Seed data

```bash
python -m scripts.seed_data
```

### 5. Start API

```bash
python main.py
```

## Agent Run Modes

### Manual one-shot execution

```bash
python -m scripts.run_agent
```

### Automatic polling mode

Set:

- `AGENT_AUTORUN=true`
- `AGENT_POLL_SECONDS=<interval>`

Then start API. Scheduler will process pending tickets automatically.

## Docker Run

Backend is expected to run with root compose:

```bash
docker compose --env-file .env.compose up --build -d
```

Required env files:

- `../.env.compose` (copy from `../.env.compose.example`)
- `.env.docker` (copy from `.env.docker.example`)

Backend container startup sequence:

1. Alembic migration (`upgrade head`)
2. Seed mock data
3. Start FastAPI service

Access:

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

## Observability and Reliability

- Structured logging with `extra_()` metadata enrichment
- Audit-first design for explainable outcomes
- Tool retries and graceful failure handling
- LLM rate-limit controls with jitter, cooldown, and backoff
- Escalation path for low-confidence or policy-unsafe decisions

## Additional Deliverable

- Failure mode analysis: `failure_modes.md`
