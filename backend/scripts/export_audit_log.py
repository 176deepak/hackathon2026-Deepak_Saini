from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import envs
from app.models.models import AgentRun, AgentStep, Ticket, ToolExecution


def _as_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC).isoformat()
        return value.isoformat()
    return str(value)


def _enum_or_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _safe_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return _as_iso(value)
    if isinstance(value, list):
        return [_safe_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _safe_jsonable(v) for k, v in value.items()}
    if hasattr(value, "value"):
        return value.value
    return str(value)


def _parse_dt(dt_raw: str | None) -> datetime | None:
    if not dt_raw:
        return None
    normalized = dt_raw.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _to_text(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    tickets = payload.get("tickets", [])

    lines: list[str] = []
    lines.append("AUDIT LOG EXPORT")
    lines.append("=" * 80)
    lines.append(f"generated_at: {payload.get('generated_at')}")
    lines.append(f"output_format: {payload.get('output_format')}")
    lines.append(f"filters: {json.dumps(payload.get('filters', {}), ensure_ascii=True)}")
    lines.append("")
    lines.append("SUMMARY")
    lines.append("-" * 80)
    lines.append(f"tickets: {summary.get('tickets')}")
    lines.append(f"runs: {summary.get('runs')}")
    lines.append(f"steps: {summary.get('steps')}")
    lines.append(f"tool_calls: {summary.get('tool_calls')}")
    lines.append(f"run_status_counts: {summary.get('run_status_counts')}")
    lines.append(f"decision_counts: {summary.get('decision_counts')}")
    lines.append("")
    lines.append("TICKETS")
    lines.append("-" * 80)

    for ticket in tickets:
        lines.append(
            f"{ticket.get('ticket_id')} | status={ticket.get('ticket_status')} | "
            f"runs={ticket.get('run_count')} | email={ticket.get('customer_email')}"
        )
        lines.append(f"subject: {ticket.get('subject')}")
        lines.append(f"expected_action: {ticket.get('expected_action')}")
        lines.append(f"latest_decision: {ticket.get('latest_final_decision')}")
        lines.append("")

        for run in ticket.get("runs", []):
            lines.append(
                f"  RUN {run.get('run_id')} | status={run.get('status')} | "
                f"decision={run.get('final_decision')} | confidence={run.get('confidence_score')}"
            )
            lines.append(
                f"  started_at={run.get('started_at')} ended_at={run.get('ended_at')} "
                f"failure_reason={run.get('failure_reason')}"
            )
            for step in run.get("steps", []):
                lines.append(
                    f"    STEP {step.get('step_number')} | action={step.get('action_type')} "
                    f"| status={step.get('status')} | tool_calls={len(step.get('tool_calls', []))}"
                )
                lines.append(f"      thought: {step.get('thought')}")
                for tool_call in step.get("tool_calls", []):
                    lines.append(
                        f"      TOOL {tool_call.get('tool_name')} | status={tool_call.get('status')} "
                        f"| error={tool_call.get('error_message')}"
                    )
            lines.append("")
        lines.append("-" * 80)

    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class ExportArgs:
    output: Path
    fmt: str
    from_dt: datetime | None
    to_dt: datetime | None
    limit: int | None
    require_processed: bool


def _build_args() -> ExportArgs:
    parser = argparse.ArgumentParser(
        description=(
            "Export complete audit logs (ticket -> runs -> steps -> tool calls) "
            "for hackathon deliverable."
        )
    )
    parser.add_argument(
        "--output",
        type=str,
        default="audit_log.json",
        help="Output file path (default: audit_log.json)",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=("json", "txt"),
        default="json",
        help="Output format: json or txt (default: json)",
    )
    parser.add_argument(
        "--from",
        dest="from_dt",
        type=str,
        default=None,
        help="Inclusive UTC start datetime (ISO 8601), e.g. 2026-04-19T05:50:00Z",
    )
    parser.add_argument(
        "--to",
        dest="to_dt",
        type=str,
        default=None,
        help="Inclusive UTC end datetime (ISO 8601), e.g. 2026-04-19T06:30:00Z",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional max number of tickets to export (ordered by ticket_id).",
    )
    parser.add_argument(
        "--include-pending",
        action="store_true",
        help="Include tickets with no runs (default: false).",
    )
    ns = parser.parse_args()

    return ExportArgs(
        output=Path(ns.output),
        fmt=ns.fmt,
        from_dt=_parse_dt(ns.from_dt),
        to_dt=_parse_dt(ns.to_dt),
        limit=ns.limit,
        require_processed=not ns.include_pending,
    )


def _make_db_url() -> str:
    return (
        f"postgresql+psycopg2://{envs.PG_DB_USER}:"
        f"{envs.PG_DB_PASSWORD}@"
        f"{envs.PG_DB_HOST}:"
        f"{envs.PG_DB_PORT}/"
        f"{envs.PG_DB_NAME}"
    )


def _export_payload(session: Session, args: ExportArgs) -> dict[str, Any]:
    tickets_stmt = select(Ticket).order_by(Ticket.external_ticket_id.asc())
    tickets = list(session.scalars(tickets_stmt).all())

    if args.limit is not None:
        tickets = tickets[: max(args.limit, 0)]

    run_status_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()

    total_runs = 0
    total_steps = 0
    total_tool_calls = 0

    ticket_items: list[dict[str, Any]] = []
    for ticket in tickets:
        runs_stmt = (
            select(AgentRun)
            .where(AgentRun.ticket_id == ticket.id)
            .order_by(AgentRun.started_at.asc())
        )
        runs = list(session.scalars(runs_stmt).all())

        if args.from_dt is not None:
            runs = [
                r
                for r in runs
                if r.started_at is not None
                and (
                    (r.started_at if r.started_at.tzinfo else r.started_at.replace(tzinfo=UTC))
                    >= args.from_dt
                )
            ]
        if args.to_dt is not None:
            runs = [
                r
                for r in runs
                if r.started_at is not None
                and (
                    (r.started_at if r.started_at.tzinfo else r.started_at.replace(tzinfo=UTC))
                    <= args.to_dt
                )
            ]

        if args.require_processed and not runs:
            continue

        run_items: list[dict[str, Any]] = []
        latest_decision: str | None = None
        for run in runs:
            run_status = str(_enum_or_value(run.status) or "")
            final_decision = run.final_decision or ""

            run_status_counts[run_status] += 1
            decision_counts[final_decision or ""] += 1
            total_runs += 1
            latest_decision = final_decision or latest_decision

            steps_stmt = (
                select(AgentStep)
                .where(AgentStep.agent_run_id == run.id)
                .order_by(AgentStep.step_number.asc(), AgentStep.created_at.asc())
            )
            steps = list(session.scalars(steps_stmt).all())

            step_items: list[dict[str, Any]] = []
            for step in steps:
                total_steps += 1
                tool_stmt = (
                    select(ToolExecution)
                    .where(ToolExecution.agent_step_id == step.id)
                    .order_by(ToolExecution.created_at.asc())
                )
                tool_rows = list(session.scalars(tool_stmt).all())
                total_tool_calls += len(tool_rows)

                tool_items = [
                    {
                        "tool_execution_id": str(tool.id),
                        "tool_name": tool.tool_name,
                        "status": _enum_or_value(tool.status),
                        "error_message": tool.error_message,
                        "retry_count": tool.retry_count,
                        "latency_ms": tool.latency_ms,
                        "created_at": _as_iso(tool.created_at),
                        "request_payload": _safe_jsonable(tool.request_payload),
                        "response_payload": _safe_jsonable(tool.response_payload),
                    }
                    for tool in tool_rows
                ]

                step_items.append(
                    {
                        "step_id": str(step.id),
                        "step_number": step.step_number,
                        "created_at": _as_iso(step.created_at),
                        "status": step.status,
                        "thought": step.thought,
                        "decision": step.decision,
                        "action_type": step.action_type,
                        "tool_name": step.tool_name,
                        "latency_ms": step.latency_ms,
                        "input_payload": _safe_jsonable(step.input_payload),
                        "output_payload": _safe_jsonable(step.output_payload),
                        "tool_calls": tool_items,
                    }
                )

            run_items.append(
                {
                    "run_id": str(run.id),
                    "status": run_status,
                    "started_at": _as_iso(run.started_at),
                    "ended_at": _as_iso(run.ended_at),
                    "final_decision": final_decision or None,
                    "confidence_score": run.confidence_score,
                    "failure_reason": run.failure_reason,
                    "total_steps": run.total_steps,
                    "total_tool_calls": run.total_tool_calls,
                    "steps": step_items,
                }
            )

        ticket_items.append(
            {
                "ticket_uuid": str(ticket.id),
                "ticket_id": ticket.external_ticket_id,
                "customer_email": ticket.customer_email,
                "subject": ticket.subject,
                "body": ticket.body,
                "expected_action": ticket.expected_action,
                "ticket_status": _enum_or_value(ticket.status),
                "created_at": _as_iso(ticket.created_at),
                "updated_at": _as_iso(ticket.updated_at),
                "resolved_at": _as_iso(ticket.resolved_at),
                "run_count": len(run_items),
                "latest_final_decision": latest_decision,
                "runs": run_items,
            }
        )

    return {
        "generated_at": _as_iso(datetime.now(tz=UTC)),
        "output_format": args.fmt,
        "source": {
            "database": envs.PG_DB_NAME,
            "host": envs.PG_DB_HOST,
            "port": envs.PG_DB_PORT,
        },
        "filters": {
            "from": _as_iso(args.from_dt),
            "to": _as_iso(args.to_dt),
            "limit": args.limit,
            "require_processed": args.require_processed,
        },
        "summary": {
            "tickets": len(ticket_items),
            "runs": total_runs,
            "steps": total_steps,
            "tool_calls": total_tool_calls,
            "run_status_counts": dict(run_status_counts),
            "decision_counts": dict(decision_counts),
        },
        "tickets": ticket_items,
    }


def main() -> None:
    args = _build_args()

    engine = create_engine(_make_db_url(), pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with SessionLocal() as session:
        payload = _export_payload(session=session, args=args)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.fmt == "txt":
        text = _to_text(payload)
        args.output.write_text(text, encoding="utf-8")
    else:
        args.output.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2, default=str),
            encoding="utf-8",
        )

    print(
        f"Export complete: {args.output} | tickets={payload['summary']['tickets']} "
        f"runs={payload['summary']['runs']} steps={payload['summary']['steps']} "
        f"tool_calls={payload['summary']['tool_calls']}"
    )


if __name__ == "__main__":
    main()

