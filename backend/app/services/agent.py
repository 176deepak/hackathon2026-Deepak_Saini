from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.agents.ticket_agent import init_ticket_resolver_agent
from app.clients.pg import get_pgdb
from app.clients.redis import get_redis, init_redis
from app.core.config import envs
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer
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
        claimed = await self._claim_pending(limit=envs.AGENT_MAX_TICKETS_PER_TICK)
        if not claimed:
            return AgentTickResult(claimed=0, succeeded=0, escalated=0, failed=0)

        sem = asyncio.Semaphore(envs.AGENT_MAX_CONCURRENCY)
        results: list[str] = []

        async def _guarded(ticket):
            async with sem:
                return await self._process_one(ticket)

        tasks = [asyncio.create_task(_guarded(t)) for t in claimed]
        for t in tasks:
            results.append(await t)

        succeeded = sum(1 for r in results if r == "resolved")
        escalated = sum(1 for r in results if r == "escalated")
        failed = sum(1 for r in results if r == "failed")

        return AgentTickResult(
            claimed=len(claimed),
            succeeded=succeeded,
            escalated=escalated,
            failed=failed,
        )

    async def _claim_pending(self, limit: int):
        def _op(session: Session):
            return TicketRepo(session).claim_pending(limit=limit)

        return await _run_sync_with_pg(_op)

    async def _process_one(self, ticket) -> str:
        ticket_id = ticket.id  # UUID string
        external_id = ticket.external_ticket_id

        def _create_run(session: Session) -> str:
            return AgentRunRepo(session).create_run(ticket_id=ticket_id).id

        run_id = await _run_sync_with_pg(_create_run)

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
            return outcome
        except Exception as e:
            logger.exception("Agent run failed", extra={"ticket_id": external_id, "run_id": run_id})
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

        await _run_sync_with_pg(_op)

    async def _mark_failed(self, *, ticket_uuid: str, run_id: str, error: str) -> None:
        def _op(session: Session) -> None:
            ticket_service = TicketService(ticket_repo=TicketRepo(session))
            ticket_service.mark_failed(ticket_uuid)
            AgentRunRepo(session).fail_run(run_id, error=error)

        await _run_sync_with_pg(_op)
