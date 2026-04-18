AUDIT_API_DOC = """# Audit API

Base path: `/api/v1/audit`

## Get Ticket Audit Timeline
- Method: `GET /{ticket_id}`
- Path param:
  - `ticket_id`: external id (`TKT-001`) or internal UUID
- Response: `RESTResponse[AuditLogData]`

`AuditLogData` contains:
- `ticket_id`
- `runs[]`
  - `run_id`, `status`, `final_decision`, `confidence_score`, `started_at`, `ended_at`
  - `steps[]`
    - `step_number`, `thought`, `action`, `status`, `created_at`
    - `tool_calls[]` with `tool_name`, `status`, `error`, `created_at`

## Error Cases
- `404` when ticket is not found
"""