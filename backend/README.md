# Backend - Autonomous Support Resolution Agent

This service powers the support resolution platform API and autonomous ticket agent.

## Responsibilities

- Ticket API and dashboard API
- Auth API (Basic Auth login issuing JWT)
- Agent orchestration and concurrent ticket processing
- Tool execution and policy-aware decisioning
- Full audit logging (run, step, and tool-call granularity)
- Scheduler-driven background polling for pending tickets

## Core Components

- `app/apis/`: FastAPI route handlers
- `app/services/`: business logic and orchestration
- `app/repositories/`: data access and persistence
- `app/agents/`: LangGraph graph, tools, prompts, nodes, and edges
- `app/clients/`: PostgreSQL and Redis clients
- `app/core/`: config, security, logging, scheduler, lifespan hooks

## Agent Workflow

1. Claim pending tickets from database.
2. Execute graph with bounded concurrency (`AGENT_MAX_CONCURRENCY`).
3. Run lookup + action tools with retry budget and fault recovery.
4. Persist:
   - agent run record
   - per-step reasoning/actions
   - tool invocation results/errors
5. Mark final ticket status (`resolved`, `escalated`, or `failed`).

## Policy Guardrails

- `search_knowledge_base` is mandatory before policy-sensitive decisions.
- `check_refund_eligibility` must execute before `issue_refund`.
- On ambiguity, low confidence, or tool failure, agent escalates with structured summary.

## Local Setup

### 1. Environment

Create `.env` from `.env.example` and fill all required values.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
alembic upgrade head
```

### 4. Seed Mock Data

```bash
python -m scripts.seed_data
```

### 5. Start API

```bash
python main.py
```

## Agent Execution

### One-shot run

```bash
python -m scripts.run_agent
```

### Scheduled run

Set in `.env`:

- `AGENT_AUTORUN=true`
- `AGENT_POLL_SECONDS=30` (or desired interval)

When API starts, scheduler will process pending tickets automatically.

## API Surface

- Auth:
  - `POST /api/v1/auth/login`
- Tickets:
  - `GET /api/v1/tickets/`
  - `GET /api/v1/tickets/{ticket_id}`
  - `GET /api/v1/tickets/{ticket_id}/status`
  - `PATCH /api/v1/tickets/{ticket_id}/status`
- Dashboard:
  - `GET /api/v1/dashboard/metrics`
  - `GET /api/v1/dashboard/recent-activity`
- Audit:
  - `GET /api/v1/audit/{ticket_id}`

## Docker

Backend service is orchestrated from root compose:

```bash
docker compose up --build -d
```

The backend container runs:

1. Alembic migrations
2. Seed script
3. FastAPI app startup

## Persistence Model

- PostgreSQL:
  - customers, products, orders, tickets
  - refunds, policy evaluations
  - agent runs, steps, tool-call logs
- Redis:
  - runtime checkpoint/session storage for agent execution state

## Operational Notes

- Structured logging is enabled with level-appropriate events (`debug`, `info`, `warning`, `error`).
- Logging fields are enriched using `extra_()` metadata for request, ticket, run, and tool context.
- Designed for explainability-first behavior: no black-box terminal outcomes.
