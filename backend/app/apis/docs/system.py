SYSTEM_HEALTH_API_DOC = """# System Health API

Base path: `/api/v1/system`

## Endpoint
- Method: `GET /health`
- Purpose: Readiness check including database connectivity.

## Response
- Type: `RESTResponse[SystemHealthData]`
- Fields:
  - `status`
  - `database`
  - `version`
  - `timestamp`
"""


SYSTEM_PING_API_DOC = """# System Ping API

Base path: `/api/v1/system`

## Endpoint
- Method: `GET /ping`
- Purpose: Lightweight liveness check.

## Response
- Type: `RESTResponse[SystemPingData]`
- Fields:
  - `message`
"""
