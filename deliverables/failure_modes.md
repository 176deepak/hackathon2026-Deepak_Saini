# Failure Modes and Recovery Design

This document describes key failure scenarios in the Autonomous Support Resolution system and how the implementation handles them in production-like conditions.

## Scope

- API service: FastAPI backend
- Agent runtime: LangGraph ticket-processing flow
- Dependencies: PostgreSQL, Redis, LLM provider (Groq/OpenAI/etc.), vector knowledge base
- Auditability: run-level, step-level, and tool-call-level logging

## Failure Mode 1: Tool Failure (Timeout, Exception, Malformed Output)

### Scenario
During tool execution (`get_order`, `get_customer`, `search_knowledge_base`, `check_refund_eligibility`, etc.), the tool can timeout, throw an exception, or return malformed data.

### Why it can happen
- External dependency latency
- Temporary database/network disruptions
- Fault injection enabled for robustness validation
- Unexpected payload shape from downstream service

### Detection
- Exception raised during tool invocation in the tool node
- Structured status tagging in audit logs (`timeout`, `failed`, `malformed`)
- Warning/error logs with `run_id`, `ticket_id`, `tool_name`, and `attempt`

### System handling
- Bounded retry loop using `AGENT_MAX_RETRIES`
- Exponential backoff between retries
- Error-to-result fallback (`{"error": ...}`) so the graph continues instead of crashing
- Tool execution persisted in audit trail even on failure
- If safe resolution is not possible after retries, agent escalates with summary

### Outcome
- Ticket processing does not crash globally
- Single-ticket degradation is isolated
- Human handoff path is preserved with traceability

---

## Failure Mode 2: LLM Provider Rate Limiting (HTTP 429)

### Scenario
The LLM provider returns `429 Too Many Requests` under free-tier limits or burst traffic.

### Why it can happen
- Parallel ticket execution causing burst LLM calls
- Strict free-tier RPM/TPM quotas
- Multi-step agent chains generating multiple completions per ticket

### Detection
- LLM invocation exception classified as rate-limit (`429`, `rate limit`, `too many requests`)
- Warning logs showing retry attempts and cooldown windows

### System handling
- Provider-specific jitter before requests (Groq path)
- LLM concurrency cap via semaphore (`AGENT_LLM_MAX_CONCURRENCY`)
- Global cooldown gate shared across concurrent tickets after a 429
- Exponential backoff with jitter (`AGENT_LLM_MAX_RETRIES`, `AGENT_LLM_BACKOFF_MAX_SECONDS`)
- Internal provider retries disabled for Groq (`max_retries=0`) to avoid retry storms

### Outcome
- Request bursts are dampened
- 429 cascades are reduced
- Agent eventually progresses or cleanly escalates/marks failed based on retry budget

---

## Failure Mode 3: Missing or Conflicting Policy Evidence

### Scenario
Ticket requires policy-sensitive decisions (refund/return/warranty/exception), but policy evidence is incomplete, ambiguous, or conflicts with customer claims.

### Why it can happen
- Customer states unsupported policy claims
- Incomplete ticket context (missing order details)
- Divergence between customer narrative and system records

### Detection
- Prompt policy guardrails detect policy-sensitive intent
- Tool outputs indicate missing data or contradictions
- Confidence drops for autonomous resolution

### System handling
- Mandatory `search_knowledge_base` before policy-based decisions
- Mandatory `check_refund_eligibility` before `issue_refund`
- Record verification via `get_order`, `get_customer`, `get_product`
- If still uncertain/unsafe, escalate with structured summary and priority
- No irreversible action taken without required checks

### Outcome
- Prevents policy-unsafe automation
- Prevents wrongful refunds and incorrect denials
- Keeps decision path explainable and reviewable

---

## Failure Mode 4: Scheduler Overlap / Long-Running Tick

### Scenario
A polling cycle runs longer than the next schedule interval.

### Why it can happen
- Large pending queue
- LLM/tool retry overhead
- External latency spikes

### Detection
- APScheduler warnings:
  - missed run time
  - max running instances reached

### System handling
- Scheduler job configured with `max_instances=1` to prevent overlapping ticks
- `coalesce=True` to avoid backlog explosion
- Per-ticket bounded concurrency using semaphore (`AGENT_MAX_CONCURRENCY`)
- Claim-and-process model isolates each tick’s workload

### Outcome
- No duplicate parallel pollers
- Stable processing under load
- Predictable degradation instead of uncontrolled fan-out

---

## Failure Mode 5: Partial Infrastructure Failure (DB/Redis Availability)

### Scenario
Database or Redis is unavailable during startup or execution.

### Why it can happen
- Service restart
- network partition
- credential/config mismatch

### Detection
- Startup checks for PostgreSQL and Redis initialization
- Explicit runtime errors when session/checkpointer dependencies are unavailable

### System handling
- Fail-fast behavior on startup initialization failure
- Container orchestration health checks (Postgres/Redis in Docker Compose)
- Agent marks ticket/run as failed when per-ticket persistence cannot complete
- Structured logs include component, layer, category, and contextual metadata

### Outcome
- Failure is explicit and diagnosable
- No silent data corruption
- Recovery is operationally straightforward once dependency is restored

---

## Operational Controls

Recommended controls for production-like operation:

- Keep `AGENT_FAULT_INJECTION=false` outside controlled demos
- Tune:
  - `AGENT_MAX_CONCURRENCY`
  - `AGENT_LLM_MAX_CONCURRENCY`
  - `AGENT_LLM_MIN_DELAY_SECONDS`
  - `AGENT_LLM_MAX_DELAY_SECONDS`
  - `AGENT_LLM_MAX_RETRIES`
- Monitor:
  - ticket outcome distribution (`resolved`, `escalated`, `failed`)
  - 429 frequency
  - tool retry counts
  - tick duration vs poll interval

## Summary

The system is designed for graceful degradation, bounded retries, policy-safe decisioning, and full observability. Failures do not terminate global processing; instead, they are isolated per ticket, audited, and routed to escalation when autonomous confidence is insufficient.
