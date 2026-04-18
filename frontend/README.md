# Frontend - Support Resolution Dashboard

This dashboard is the operational UI for the autonomous support agent platform.

## Features

- Login page with backend Basic Auth integration (`/auth/login`) and JWT handling
- Dashboard metrics (`total`, `resolved`, `escalated`, `failed`)
- Ticket listing with selectable ticket detail panel
- Audit timeline view for selected ticket (runs, steps, tool calls)
- Recent activity panel with:
  - initial limit (3 items)
  - `Load More` pagination
  - scrollable list container
- Protected API access using bearer token for all secured endpoints

## Tech Stack

- React 19
- Vite 8
- Plain CSS (KSolves-aligned color system: red, dark grey, white)
- REST API integration against backend `/api/v1`

## Environment Variables

Create `.env` from `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_VERSION=1
```

Note: Vite injects `VITE_*` values at build time.

## Local Development

```bash
npm install
npm run dev
```

Default local URL:

- `http://localhost:5173`

## Production Build

```bash
npm run build
npm run preview
```

## Docker

Frontend uses a multi-stage Docker build:

1. `node:22-alpine` for building static assets
2. `nginx:alpine` for serving production build

Run via root compose:

```bash
docker compose up --build -d
```

The frontend is exposed at:

- `http://localhost:5173`

## API Integration Map

- Auth:
  - `POST /api/v1/auth/login`
- Dashboard:
  - `GET /api/v1/dashboard/metrics`
  - `GET /api/v1/dashboard/recent-activity`
- Tickets:
  - `GET /api/v1/tickets/`
  - `GET /api/v1/tickets/{ticket_id}`
  - `GET /api/v1/tickets/{ticket_id}/status`
  - `PATCH /api/v1/tickets/{ticket_id}/status`
- Audit:
  - `GET /api/v1/audit/{ticket_id}`
