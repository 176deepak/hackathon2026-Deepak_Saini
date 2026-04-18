DASHBOARD_API_DOC = """# Dashboard API

Base path: `/api/v1/dashboard`

## Metrics
- Method: `GET /metrics`
- Returns aggregate counters:
  - `total_tickets`
  - `resolved`
  - `escalated`
  - `failed`
- Response: `RESTResponse[DashboardMetricsData]`

## Recent Activity
- Method: `GET /recent-activity`
- Query params:
  - `limit` (default: `10`, max: `50`)
- Response: `RESTResponse[DashboardRecentActivityData]`
- Activity item fields:
  - `ticket_id`
  - `status`
  - `subject`
  - `updated_at`
"""