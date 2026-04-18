DASHBOARD_METRICS_API_DOC = """# Dashboard Metrics API

Base path: `/api/v1/dashboard`

## Endpoint
- Method: `GET /metrics`
- Purpose: Fetch aggregate ticket counters.

## Response
- Type: `RESTResponse[DashboardMetricsData]`
- Fields:
  - `total_tickets`
  - `resolved`
  - `escalated`
  - `failed`
"""


DASHBOARD_RECENT_ACTIVITY_API_DOC = """# Dashboard Recent Activity API

Base path: `/api/v1/dashboard`

## Endpoint
- Method: `GET /recent-activity`
- Purpose: Fetch latest ticket updates.

## Query Params
- `limit` (default: `10`, max: `50`)

## Response
- Type: `RESTResponse[DashboardRecentActivityData]`
- Item fields:
  - `ticket_id`
  - `status`
  - `subject`
  - `updated_at`
"""
