# Autonomous Support Resolution Platform

Full-stack implementation of the KSolves Agentic AI Hackathon problem statement for autonomous support ticket handling.

## Platform Overview

This repository contains two applications:

- `backend/`: FastAPI service with LangGraph agent orchestration, policy-aware tool execution, audit persistence, and scheduler-driven processing of pending tickets.
- `frontend/`: React dashboard for authentication, ticket operations, status tracking, and audit timeline inspection.

## Demo Assets

### Dashboard Screens

![Dashboard - View 1](assets/Screenshot%202026-04-19%20102826.png)
![Dashboard - View 2](assets/Screenshot%202026-04-19%20102837.png)

### Architecture/DB Snapshot

![Architecture DB Snapshot](deliverables/Shopwave%20Ticket%20Resolvr%20DB.png)

### Demo Video

- `deliverables/shopwave.mp4`

## High-Level Architecture

```text
[React Dashboard] --> [FastAPI APIs + Agent Runtime] --> [PostgreSQL]
                               |                          [Redis]
                               +--> [LLM Provider + KB Search]
```

## Tech Stack

- Frontend: React 19, Vite 8, CSS
- Backend: Python 3.12, FastAPI, SQLAlchemy, Alembic, APScheduler
- Agent Runtime: LangGraph, LangChain tools
- Datastores: PostgreSQL (system of record), Redis (session/checkpoint/runtime state)
- Search/Policy Context: Chroma-backed knowledge base retrieval
- Deployment: Docker, Docker Compose

## Agent Workflow Summary

1. Poller claims `pending` tickets from PostgreSQL.
2. Each ticket runs through the LangGraph flow with bounded concurrency.
3. Agent executes tool chains for lookup, policy checks, and actions.
4. Every run writes:
   - run metadata
   - reasoning steps
   - tool invocation logs (status/error/output)
5. Ticket is finalized as `resolved`, `escalated`, or `failed`.

## Deliverables Index

- Backend service documentation: `backend/README.md`
- Frontend dashboard documentation: `frontend/README.md`
- Failure mode analysis: `backend/failure_modes.md`
- Compose deployment: `docker-compose.yml`
- Demo recording: `deliverables/shopwave.mp4`

## Quick Start (Docker)

### Prerequisites

- Docker Desktop or Docker Engine with Compose v2
- `backend/.env.docker` configured (copy from `backend/.env.docker.example`)
- root `.env.compose` configured (copy from `.env.compose.example`)

### Run

Create env files first:

```bash
cp .env.compose.example .env.compose
cp backend/.env.docker.example backend/.env.docker
```

Then start:

```bash
docker compose --env-file .env.compose up --build -d
```

### Access

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### Stop

```bash
docker compose --env-file .env.compose down
```

### Clean volumes

```bash
docker compose --env-file .env.compose down -v
```

## Repository Structure

```text
.
|-- backend/
|-- frontend/
|-- assets/
|-- deliverables/
|-- docker-compose.yml
`-- README.md
```

## Deliverables
> [README](README.md)
> 
> [Agent Architecture](/deliverables/architecture.pdf)
>
> [Agent Failure Modes](/deliverables/failure_modes.md)
> 
> [Audit Logs JSON](/deliverables/audit_log.json)
> [Audit Logs TXT](/deliverables/audit_log.txt)
> 
> [Recorded Demo](/deliverables/shopwave.mp4)
