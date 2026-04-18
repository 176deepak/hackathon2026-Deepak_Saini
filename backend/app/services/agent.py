from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.agents.ticket_agent import init_ticket_resolver_agent
from app.clients.pg import get_pgdb
from app.clients.redis import get_redis, init_redis
from app.core.config import envs
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
from app.repositories.agent import AgentRunRepo
from app.repositories.ticket import TicketRepo
from app.services.tickets import TicketService

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.SERVICE,
        "category": LogCategory.AGENT,
        "component": __name__,
    },
)


async def _run_sync_with_pg(op):
    async for async_session in get_pgdb():
        return await async_session.run_sync(op)
    raise RuntimeError("Unable to acquire database session")


_graph = None
_graph_lock = asyncio.Lock()


async def _get_graph():
    global _graph
    if _graph is not None:
        return _graph
    async with _graph_lock:
        if _graph is None:
            # If we're running outside FastAPI lifespan (e.g., CLI), Redis may not
            # be initialized yet.
            try:
                _ = get_redis()
            except Exception:
                await init_redis()
            _graph = await init_ticket_resolver_agent()
        return _graph


@dataclass(frozen=True)
class AgentTickResult:
    claimed: int
    succeeded: int
    escalated: int
    failed: int


class AgentRunner:
    """Poll pending tickets, run the agent concurrently, and persist audit trail."""

    async def run_tick(self) -> AgentTickResult:
        logger.info(
            "Agent tick started",
            extra=extra_(
                operation="agent_tick",
                status="start",
                poll_seconds=envs.AGENT_POLL_SECONDS,
                max_concurrency=envs.AGENT_MAX_CONCURRENCY,
                max_tickets_per_tick=envs.AGENT_MAX_TICKETS_PER_TICK,
            ),
        )

        claimed = await self._claim_pending(limit=envs.AGENT_MAX_TICKETS_PER_TICK)
        if not claimed:
            logger.debug(
                "No pending tickets claimed",
                extra=extra_(operation="agent_tick", status="skipped", claimed=0),
            )
            return AgentTickResult(claimed=0, succeeded=0, escalated=0, failed=0)

        sem = asyncio.Semaphore(envs.AGENT_MAX_CONCURRENCY)
        results: list[str] = []

        async def _guarded(ticket):
            async with sem:
                return await self._process_one(ticket)

        tasks = [asyncio.create_task(_guarded(t)) for t in claimed]
        # gather() waits for all tasks; _process_one handles per-ticket failures.
        results = await asyncio.gather(*tasks)

        succeeded = sum(1 for r in results if r == "resolved")
        escalated = sum(1 for r in results if r == "escalated")
        failed = sum(1 for r in results if r == "failed")

        logger.info(
            "Agent tick completed",
            extra=extra_(
                operation="agent_tick",
                status="success",
                claimed=len(claimed),
                resolved=succeeded,
                escalated=escalated,
                failed=failed,
            ),
        )

        return AgentTickResult(
            claimed=len(claimed),
            succeeded=succeeded,
            escalated=escalated,
            failed=failed,
        )

    async def _claim_pending(self, limit: int):
        def _op(session: Session):
            return TicketRepo(session).claim_pending(limit=limit)

        try:
            claimed = await _run_sync_with_pg(_op)
            logger.debug(
                "Claimed pending tickets",
                extra=extra_(
                    operation="claim_pending",
                    status="success",
                    limit=limit,
                    claimed=len(claimed),
                ),
            )
            return claimed
        except Exception:
            logger.exception(
                "Failed to claim pending tickets",
                extra=extra_(operation="claim_pending", status="failure", limit=limit),
            )
            raise

    async def _process_one(self, ticket) -> str:
        ticket_id = ticket.id  # UUID string
        external_id = ticket.external_ticket_id
        logger.info(
            "Processing ticket",
            extra=extra_(operation="process_ticket", status="start", ticket_id=external_id),
        )

        def _create_run(session: Session) -> str:
            return AgentRunRepo(session).create_run(ticket_id=ticket_id).id

        try:
            run_id = await _run_sync_with_pg(_create_run)
        except Exception:
            logger.exception(
                "Failed to create agent run",
                extra=extra_(operation="agent_run", status="failure", ticket_id=external_id),
            )
            # Ticket is currently "processing" since it was claimed; mark failed so it doesn't get stuck.
            await self._mark_failed(
                ticket_uuid=ticket_id,
                run_id="unknown",
                error="create_run_failed",
            )
            return "failed"

        graph = await _get_graph()

        # Minimal state expected by your graph + audit nodes.
        state = {
            "ticket": {
                "ticket_id": external_id,
                "customer_email": ticket.customer_email,
                "subject": ticket.subject,
                "body": ticket.body,
            },
            "messages": [],
            "total_step": 0,
            "final_response": None,
            "run_id": run_id,
            "current_step_id": None,
            "tool_calls_made": 0,
        }

        try:
            final_state = await graph.ainvoke(
                state,
                config={"configurable": {"run_id": run_id}},
            )
            outcome = self._infer_outcome(final_state)
            await self._finalize_ticket_and_run(
                ticket_uuid=ticket_id,
                run_id=run_id,
                outcome=outcome,
            )
            logger.info(
                "Ticket processed",
                extra=extra_(
                    operation="process_ticket",
                    status="success",
                    ticket_id=external_id,
                    run_id=run_id,
                    outcome=outcome,
                ),
            )
            return outcome
        except Exception as e:
            logger.exception(
                "Agent run failed",
                extra=extra_(
                    operation="process_ticket",
                    status="failure",
                    ticket_id=external_id,
                    run_id=run_id,
                    error_type=type(e).__name__,
                ),
            )
            await self._mark_failed(ticket_uuid=ticket_id, run_id=run_id, error=str(e))
            return "failed"

    def _infer_outcome(self, final_state) -> str:
        # Look for the last terminal tool call in the message stream.
        terminal_tools = {"send_reply", "issue_refund", "escalate"}
        last_terminal = None
        for m in final_state.get("messages", []):
            name = getattr(m, "name", None)
            if name in terminal_tools:
                last_terminal = name

        if last_terminal == "escalate":
            return "escalated"
        if last_terminal in {"send_reply", "issue_refund"}:
            return "resolved"
        # Fallback: if no terminal tool was called, treat as failed (for scoring).
        return "failed"

    async def _finalize_ticket_and_run(self, *, ticket_uuid: str, run_id: str, outcome: str) -> None:
        def _op(session: Session) -> None:
            ticket_repo = TicketRepo(session)
            ticket_service = TicketService(ticket_repo=ticket_repo)

            run_repo = AgentRunRepo(session)

            if outcome == "resolved":
                ticket_service.mark_resolved(ticket_uuid)
                run_repo.complete_run(run_id, "completed", decision="resolved", confidence=0.85)
            elif outcome == "escalated":
                ticket_service.mark_escalated(ticket_uuid)
                run_repo.complete_run(run_id, "escalated", decision="escalated", confidence=0.35)
            else:
                ticket_service.mark_failed(ticket_uuid)
                run_repo.fail_run(run_id, error="No terminal action taken")

        try:
            await _run_sync_with_pg(_op)
            logger.debug(
                "Finalized ticket/run",
                extra=extra_(
                    operation="finalize_ticket",
                    status="success",
                    run_id=run_id,
                    outcome=outcome,
                ),
            )
        except Exception:
            logger.exception(
                "Failed to finalize ticket/run",
                extra=extra_(
                    operation="finalize_ticket",
                    status="failure",
                    run_id=run_id,
                    outcome=outcome,
                ),
            )
            raise

    async def _mark_failed(self, *, ticket_uuid: str, run_id: str, error: str) -> None:
        def _op(session: Session) -> None:
            ticket_service = TicketService(ticket_repo=TicketRepo(session))
            ticket_service.mark_failed(ticket_uuid)
            AgentRunRepo(session).fail_run(run_id, error=error)

        try:
            await _run_sync_with_pg(_op)
            logger.warning(
                "Marked ticket/run as failed",
                extra=extra_(operation="mark_failed", status="success", run_id=run_id),
            )
        except Exception:
            logger.exception(
                "Failed to mark ticket/run as failed",
                extra=extra_(operation="mark_failed", status="failure", run_id=run_id),
            )
