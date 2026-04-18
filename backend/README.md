# ShopWave - Autonomous Support Resolution Agent (Hackathon 2026)

This repo is a backend for an "autonomous support resolution agent" that:
1. Ingests tickets from a simulated source (seed data)
2. Classifies and triages tickets
3. Resolves tickets autonomously using tools (refund, reply) when safe
4. Escalates intelligently when uncertain
5. Audits every decision (steps + tool calls), not just the final answer

## Quick Start (Local)

### 1) Configure env
Create `.env` based on `.env.example` and fill in:
- `APP_*` settings (host/port/logs)
- `PG_*` settings (Postgres)
- Provider keys if you use LLM/KG tooling: `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`

### 2) Seed mock data
```powershell
python -m scripts.seed_data
```

### 3) Run API
```powershell
python main.py
```

API base path:
- `/api/v{APP_APIS_VERSION}/tickets`
- `/api/v{APP_APIS_VERSION}/dashboard`
- `/api/v{APP_APIS_VERSION}/audit/{ticket_id}`

Docs are protected by basic auth:
- `/docs`
- `/redoc`

## Demo Expectations (Hackathon)
The problem statement expects the agent to:
- Use at least 3 tool calls in a single reasoning chain per ticket.
- Process tickets concurrently (not sequentially).
- Recover from tool failures (timeouts/malformed outputs) without crashing.
- Produce explainable decisions.
- Log tool calls, reasoning, and outcomes (audit trail).

This repo already contains the tool surface and audit schema; the next step is wiring an agent runner that processes all pending tickets end-to-end with concurrency + retries + auditing.
