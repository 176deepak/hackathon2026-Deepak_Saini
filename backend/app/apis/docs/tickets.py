
TICKETS_API_DOC = """# Tickets API

Base path: `/api/v1/tickets`

## List Tickets
- Method: `GET /`
- Query params:
  - `status` (optional): `pending|processing|resolved|escalated|waiting_for_customer|failed`
  - `page` (default: `1`)
  - `limit` (default: `20`, max: `100`)
- Response: `RESTResponse[TicketListData]`

## Get Ticket
- Method: `GET /{ticket_id}`
- Path param:
  - `ticket_id`: external id (`TKT-001`) or internal UUID
- Response: `RESTResponse[TicketDetailData]`

## Get Ticket Status
- Method: `GET /{ticket_id}/status`
- Response: `RESTResponse[TicketStatusData]`

## Update Ticket Status
- Method: `PATCH /{ticket_id}/status`
- Request body:
```json
{
  "status": "processing"
}
```
- Response: `RESTResponse[TicketStatusData]`

## Error Cases
- `404` when ticket is not found
- `422` for invalid query/body values
"""