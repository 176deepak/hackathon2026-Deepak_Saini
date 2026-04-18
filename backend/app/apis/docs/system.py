SYSTEM_API_DOC = """# System API

Base path: `/api/v1/system`

## Health
- Method: `GET /health`
- Description: readiness check (includes DB query `SELECT 1`)
- Response: `RESTResponse[SystemHealthData]`
  - `status`
  - `database`
  - `version`
  - `timestamp`

## Ping
- Method: `GET /ping`
- Description: lightweight liveness check
- Response: `RESTResponse[SystemPingData]`
"""