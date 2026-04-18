import asyncio
import json
import logging
import random
from typing import Any

from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
from sqlalchemy.orm import Session

from app.agents.prompts import TICKET_AGENT_SYSTEM_PROMPT
from app.agents.schemas import TicketAgentState
from app.agents.tools.registry import ticket_agent_tools, ticket_agent_tools_mapper
from app.agents.utils.utils import get_chat_llm
from app.clients.pg import get_pgdb
from app.core.config import envs
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
from app.repositories.agent import AgentStepRepo, ToolExecutionRepo

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.AGENT,
        "category": LogCategory.AGENT,
        "component": __name__,
    },
)


_base_llm = get_chat_llm(envs.LLM_PROVIDER, envs.LLM_MODEL)
llm = _base_llm.bind_tools(ticket_agent_tools)


async def _run_sync_with_pg(op):
    async for async_session in get_pgdb():
        return await async_session.run_sync(op)
    raise RuntimeError("Unable to acquire database session")


def _json_dumps(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=True, default=str)
    except Exception:
        return json.dumps(str(value), ensure_ascii=True)


def _fault_injection_result() -> tuple[bool, dict[str, Any] | None, Exception | None]:
    """Return (did_inject, result, error)."""
    mode = random.choice(["timeout", "malformed"])
    if mode == "timeout":
        return True, None, TimeoutError("Simulated tool timeout")
    return True, {"malformed": True, "raw": "<<<garbage>>>"}, None


async def reasoning_node(state: TicketAgentState) -> TicketAgentState:
    tool_calls_made = int(state.get("tool_calls_made") or 0)
    prompt = TICKET_AGENT_SYSTEM_PROMPT.render(
        ticket=state["ticket"],
        tool_calls_made=tool_calls_made,
    )

    history = list(state.get("messages") or [])
    
    if not len(history):
        history.append(HumanMessage(content="Let's start"))
    
    response = await llm.ainvoke([SystemMessage(content=prompt), *history])
    logger.debug(
        "LLM reasoning completed",
        extra=extra_(
            operation="agent_reasoning",
            status="success",
            run_id=state.get("run_id"),
            ticket_id=state.get("ticket", {}).get("ticket_id"),
            tool_calls_planned=len(response.tool_calls or []),
        ),
    )

    planned = [
        {"name": c.get("name"), "args": c.get("args")}
        for c in (response.tool_calls or [])
    ]
    thought = (
        f"Planned tool calls: {planned}"
        if planned
        else (response.content or "No tool calls; final response.")
    )

    # Create a step row for this reasoning decision.
    step_number = int(state.get("total_step") or 0) + 1
    step_id: str | None = None

    def _op(session: Session) -> str:
        return AgentStepRepo(session).log_step(
            run_id=state["run_id"],
            step_number=step_number,
            thought=thought,
            action="reasoning",
            input_payload={"prompt": prompt},
            output_payload={"tool_calls": planned, "content": response.content},
            status="success",
        )

    try:
        step_id = await _run_sync_with_pg(_op)
    except Exception:
        # Audit failures should never crash the agent.
        logger.exception(
            "Failed to write reasoning step audit",
            extra=extra_(
                operation="audit_reasoning",
                status="failure",
                run_id=state.get("run_id"),
                ticket_id=state.get("ticket", {}).get("ticket_id"),
            ),
        )

    return {
        "messages": [response],
        "total_step": step_number,
        "current_step_id": step_id,
    }


async def tool_node(state: TicketAgentState) -> TicketAgentState:
    outputs: list[ToolMessage] = []

    current_step_id = state.get("current_step_id")
    tool_calls_made = int(state.get("tool_calls_made") or 0)
    injected_already = bool(state.get("_fault_injected") or False)

    cfg = {
        "configurable": {
            "thread_id": state.get("thread_id"),
            "run_id": state.get("run_id"),
        }
    }

    for tool_call in state["messages"][-1].tool_calls:
        name = tool_call["name"]
        args = tool_call.get("args") or {}
        tool_calls_made += 1
        logger.debug(
            "Tool call requested",
            extra=extra_(
                operation="tool_call",
                status="start",
                run_id=state.get("run_id"),
                ticket_id=state.get("ticket", {}).get("ticket_id"),
                tool_name=name,
                attempt_max=envs.AGENT_MAX_RETRIES,
            ),
        )

        # Retry budget with exponential backoff.
        last_err: str | None = None
        result: dict[str, Any] | None = None

        last_exc: Exception | None = None
        for attempt in range(envs.AGENT_MAX_RETRIES + 1):
            try:
                # Force one realistic failure per ticket run to prove recovery.
                if envs.AGENT_FAULT_INJECTION and not injected_already:
                    injected_already, injected_result, injected_error = (
                        _fault_injection_result()
                    )
                    if injected_error is not None:
                        raise injected_error
                    result = injected_result
                    break

                tool = ticket_agent_tools_mapper[name]
                result = await tool.ainvoke(args, config=cfg)
                break
            except Exception as e:
                last_exc = e
                last_err = f"{type(e).__name__}: {e}"
                logger.warning(
                    "Tool call attempt failed",
                    extra=extra_(
                        operation="tool_call",
                        status="retrying" if attempt < envs.AGENT_MAX_RETRIES else "failure",
                        run_id=state.get("run_id"),
                        ticket_id=state.get("ticket", {}).get("ticket_id"),
                        tool_name=name,
                        attempt=attempt,
                        error_type=type(e).__name__,
                    ),
                )
                if attempt >= envs.AGENT_MAX_RETRIES:
                    result = {"error": last_err}
                    break
                await asyncio.sleep(min(0.5 * (2**attempt), 3.0))

        if isinstance(result, dict) and result.get("malformed") is True:
            status = "malformed"
        elif isinstance(last_exc, TimeoutError):
            status = "timeout"
        else:
            status = "success" if isinstance(result, dict) and "error" not in result else "failed"
        error = result.get("error") if isinstance(result, dict) else None

        # Persist tool execution audit linked to the reasoning step.
        if current_step_id:
            def _op(session: Session) -> None:
                ToolExecutionRepo(session).log_tool_call(
                    step_id=current_step_id,
                    tool_name=name,
                    request=args,
                    response=result if isinstance(result, dict) else {"result": result},
                    status=status,
                    error=error,
                )

            try:
                await _run_sync_with_pg(_op)
            except Exception:
                logger.exception(
                    "Failed to write tool execution audit",
                    extra=extra_(
                        operation="audit_tool",
                        status="failure",
                        run_id=state.get("run_id"),
                        ticket_id=state.get("ticket", {}).get("ticket_id"),
                        tool_name=name,
                    ),
                )

        logger.info(
            "Tool call completed",
            extra=extra_(
                operation="tool_call",
                status="success" if status == "success" else "failure",
                run_id=state.get("run_id"),
                ticket_id=state.get("ticket", {}).get("ticket_id"),
                tool_name=name,
                tool_status=status,
            ),
        )

        outputs.append(
            ToolMessage(
                content=_json_dumps(result),
                name=name,
                tool_call_id=tool_call["id"],
            )
        )

    return {
        "messages": outputs,
        "tool_calls_made": tool_calls_made,
        "_fault_injected": injected_already,
    }
