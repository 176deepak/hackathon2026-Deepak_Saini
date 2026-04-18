# Autonomous Support Resolution Platform

This repository contains a full-stack implementation of the KSolves Agentic AI Hackathon problem statement:

- `backend/`: FastAPI service, LangGraph-based autonomous ticket agent, PostgreSQL persistence, Redis-backed session/checkpoint state, audit pipeline.
- `frontend/`: React dashboard for authentication, ticket operations, recent activity, and audit timeline.

## Architecture Overview

```text
+--------------------+         +---------------------------+
| React Dashboard    |  HTTP   | FastAPI Backend           |
| (frontend, Nginx)  +-------->+ /auth /tickets /dashboard |
+--------------------+         | /audit /agent             |
                               +-------------+-------------+
                                             |
                           +-----------------+------------------+
                           |                                    |
                    +------+-------+                     +------+------+
                    | PostgreSQL   |                     | Redis       |
                    | tickets/runs |                     | session +    |
                    | audit/logs   |                     | checkpoints  |
                    +--------------+                     +-------------+
```

## Tech Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy, Alembic, APScheduler
- Agent: LangGraph + LangChain tools, tool-call audit persistence
- Data Stores: PostgreSQL (system of record), Redis (runtime state/session)
- Frontend: React + Vite, production served via Nginx
- Deployment: Docker Compose

## Agent Workflow Architecture

1. Ticket polling service claims `pending` tickets from DB.
2. Agent graph executes with bounded concurrency and retries.
3. Tool chain performs:
   - lookup (`get_customer`, `get_order`, `get_product`, `search_knowledge_base`)
   - policy checks (`check_refund_eligibility`)
   - action (`send_reply`, `issue_refund`, `escalate`)
4. Every step is written to audit tables:
   - run-level metadata
   - step-level thought/action/result
   - tool-call-level outcome and errors
5. Ticket terminal status is saved as `resolved`, `escalated`, or `failed`.

## Docker Deployment

The root `docker-compose.yml` starts:

- `postgres` on `localhost:5432`
- `redis` on `localhost:6379`
- `backend` on `localhost:8000`
- `frontend` on `localhost:5173`

### 1. Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- A valid backend env file at `backend/.env`

### 2. Start All Services

```bash
docker compose up --build -d
```

### 3. Access

- Frontend Dashboard: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- OpenAPI Docs: `http://localhost:8000/docs`

### 4. Stop

```bash
docker compose down
```

To remove persistent DB/Redis data:

```bash
docker compose down -v
```

## Repository Layout

```text
.
+-- backend/
|   +-- app/
|   |   +-- agents/
|   |   +-- apis/
|   |   +-- repositories/
|   |   +-- services/
|   |   +-- core/
|   +-- alembic/
|   +-- scripts/
|   +-- README.md
+-- frontend/
|   +-- src/
|   +-- Dockerfile
|   +-- nginx.conf
|   +-- README.md
+-- docker-compose.yml
```

## Notes

- Redis is used as runtime session/checkpoint storage (local in-memory session storage removed).
- PostgreSQL stores tickets, runs, and complete audit traces for explainability.
- Frontend calls protected APIs with bearer token returned by backend auth.
