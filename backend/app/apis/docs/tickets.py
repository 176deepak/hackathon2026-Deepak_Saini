TICKETS_LIST_API_DOC = """# Tickets List API

Base path: `/api/v1/tickets`

## Endpoint
- Method: `GET /`
- Purpose: List support tickets.

## Query Params
- `status` (optional): `pending|processing|resolved|escalated|waiting_for_customer|failed`
- `page` (default: `1`)
- `limit` (default: `20`, max: `100`)

## Response
- Type: `RESTResponse[TicketListData]`
"""


TICKETS_GET_API_DOC = """# Ticket Detail API

Base path: `/api/v1/tickets`

## Endpoint
- Method: `GET /{ticket_id}`
- Purpose: Fetch one ticket by external id or UUID.

## Response
- Type: `RESTResponse[TicketDetailData]`

## Error Cases
- `404` when ticket is not found
"""


TICKETS_STATUS_GET_API_DOC = """# Ticket Status API

Base path: `/api/v1/tickets`

## Endpoint
- Method: `GET /{ticket_id}/status`
- Purpose: Fetch current ticket workflow status.

## Response
- Type: `RESTResponse[TicketStatusData]`

## Error Cases
- `404` when ticket is not found
"""


TICKETS_STATUS_UPDATE_API_DOC = """# Ticket Status Update API

Base path: `/api/v1/tickets`

## Endpoint
- Method: `PATCH /{ticket_id}/status`
- Purpose: Update ticket workflow status.

## Request Body
```json
{
  "status": "processing"
}
```

## Response
- Type: `RESTResponse[TicketStatusData]`

## Error Cases
- `404` when ticket is not found
- `422` for invalid body values
"""
