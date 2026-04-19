# Frontend - Support Resolution Dashboard

Production-oriented React dashboard for operating and monitoring the autonomous support agent system.

## Overview

The frontend provides:

- Login/authentication flow
- KPI metrics overview
- Ticket table and ticket detail panel
- Manual ticket status update flow
- Recent activity panel with incremental loading
- Audit timeline for selected ticket runs, steps, and tool calls

## Tech Stack

- React 19
- Vite 8
- JavaScript (ES modules)
- CSS
- Nginx (container runtime for production build)

## Environment Configuration

Create `.env` from `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_VERSION=1
```

Notes:

- Only `VITE_*` variables are exposed to the frontend.
- Variables are injected at build time.

## Run Locally

### Prerequisites

- Node.js 20+ (recommended 22)
- npm
- Backend API running and reachable

### Commands

```bash
npm install
npm run dev
```

Local URL:

- `http://localhost:5173`

## Build and Preview

```bash
npm run build
npm run preview
```

## Run with Docker (Standalone Frontend)

Build image:

```bash
docker build \
  --build-arg VITE_API_BASE_URL=http://localhost:8000 \
  --build-arg VITE_API_VERSION=1 \
  -t ksolves-frontend .
```

Run container:

```bash
docker run --rm -p 5173:80 ksolves-frontend
```

Access:

- `http://localhost:5173`

## Run with Full Stack Compose

From repository root:

```bash
docker compose --env-file .env.compose up --build -d
```

This starts frontend with backend, PostgreSQL, and Redis.

## API Dependencies

The dashboard integrates with:

- `POST /api/v1/auth/login`
- `GET /api/v1/dashboard/metrics`
- `GET /api/v1/dashboard/recent-activity`
- `GET /api/v1/tickets/`
- `GET /api/v1/tickets/{ticket_id}`
- `GET /api/v1/tickets/{ticket_id}/status`
- `PATCH /api/v1/tickets/{ticket_id}/status`
- `GET /api/v1/audit/{ticket_id}`
