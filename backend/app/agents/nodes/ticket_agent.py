# import asyncio
# import json
# import logging
# import random
# import time
# from typing import Any

# from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
# from sqlalchemy.orm import Session

# from app.agents.prompts import TICKET_AGENT_SYSTEM_PROMPT
# from app.agents.schemas import TicketAgentState
# from app.agents.tools.registry import ticket_agent_tools, ticket_agent_tools_mapper
# from app.agents.utils.utils import get_chat_llm
# from app.clients.pg import get_pgdb
# from app.core.config import envs
# from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
# from app.repositories.agent import AgentStepRepo, ToolExecutionRepo

# logger = AppLoggerAdapter(
#     logging.getLogger(__name__),
#     {
#         "layer": LogLayer.AGENT,
#         "category": LogCategory.AGENT,
#         "component": __name__,
#     },
# )


# _base_llm = get_chat_llm(envs.LLM_PROVIDER, envs.LLM_MODEL)
# llm = _base_llm.bind_tools(ticket_agent_tools)
# _llm_semaphore = asyncio.Semaphore(max(1, int(envs.AGENT_LLM_MAX_CONCURRENCY)))
# _rate_limit_lock = asyncio.Lock()
# _rate_limited_until_monotonic: float = 0.0


# async def _run_sync_with_pg(op):
#     async for async_session in get_pgdb():
#         return await async_session.run_sync(op)
#     raise RuntimeError("Unable to acquire database session")


# def _json_dumps(value: Any) -> str:
#     try:
#         return json.dumps(value, ensure_ascii=True, default=str)
#     except Exception:
#         return json.dumps(str(value), ensure_ascii=True)


# def _fault_injection_result() -> tuple[bool, dict[str, Any] | None, Exception | None]:
#     """Return (did_inject, result, error)."""
#     mode = random.choice(["timeout", "malformed"])
#     if mode == "timeout":
#         return True, None, TimeoutError("Simulated tool timeout")
#     return True, {"malformed": True, "raw": "<<<garbage>>>"}, None


# def _is_rate_limit_error(exc: Exception) -> bool:
#     text = f"{type(exc).__name__}: {exc}".lower()
#     return (
#         "429" in text
#         or "too many request" in text
#         or "too many requests" in text
#         or "rate limit" in text
#         or "ratelimit" in text
#     )


# async def _call_llm_with_rate_limit_control(messages, state: TicketAgentState):
#     global _rate_limited_until_monotonic

#     provider = (envs.LLM_PROVIDER or "").strip().lower()
#     max_retries = max(0, int(envs.AGENT_LLM_MAX_RETRIES))
#     min_delay = max(0.0, float(envs.AGENT_LLM_MIN_DELAY_SECONDS))
#     max_delay = max(min_delay, float(envs.AGENT_LLM_MAX_DELAY_SECONDS))
#     max_backoff = max(1.0, float(envs.AGENT_LLM_BACKOFF_MAX_SECONDS))

#     last_exc: Exception | None = None
#     for attempt in range(max_retries + 1):
#         # Global cooldown gate shared across concurrent tickets.
#         while True:
#             async with _rate_limit_lock:
#                 wait_for = _rate_limited_until_monotonic - time.monotonic()
#             if wait_for <= 0:
#                 break
#             logger.warning(
#                 "Waiting for global LLM cooldown window",
#                 extra=extra_(
#                     run_id=state.get("run_id"),
#                     ticket_id=state.get("ticket", {}).get("ticket_id"),
#                     llm_provider=provider,
#                     wait_seconds=round(wait_for, 3),
#                 ),
#             )
#             await asyncio.sleep(min(wait_for, 60))

#         try:
#             async with _llm_semaphore:
#                 # Stagger requests for Groq free-tier to reduce burst 429 responses.
#                 if provider == "groq":
#                     delay = random.uniform(min_delay, max_delay)
#                     if delay > 0:
#                         await asyncio.sleep(delay)
#                 return await llm.ainvoke(messages)
#         except Exception as exc:
#             last_exc = exc
#             if not _is_rate_limit_error(exc) or attempt >= max_retries:
#                 raise

#             # Exponential backoff with jitter for 429/rate-limit failures.
#             backoff = min((2**attempt) + random.uniform(0.25, 1.0), max_backoff)
#             async with _rate_limit_lock:
#                 _rate_limited_until_monotonic = max(
#                     _rate_limited_until_monotonic,
#                     time.monotonic() + backoff,
#                 )
#             logger.warning(
#                 "LLM rate limited, retrying with backoff",
#                 extra=extra_(
#                     run_id=state.get("run_id"),
#                     ticket_id=state.get("ticket", {}).get("ticket_id"),
#                     llm_provider=provider,
#                     llm_model=envs.LLM_MODEL,
#                     attempt=attempt,
#                     max_retries=max_retries,
#                     sleep_seconds=round(backoff, 3),
#                     error_type=type(exc).__name__,
#                 ),
#             )
#             await asyncio.sleep(backoff)

#     if last_exc is not None:
#         raise last_exc
#     raise RuntimeError("LLM invocation failed without exception")


# async def reasoning_node(state: TicketAgentState) -> TicketAgentState:
#     tool_calls_made = int(state.get("tool_calls_made") or 0)
#     prompt = TICKET_AGENT_SYSTEM_PROMPT.render(
#         ticket=state["ticket"],
#         tool_calls_made=tool_calls_made,
#     )

#     history = list(state.get("messages") or [])
    
#     if not len(history):
#         history.append(HumanMessage(content="Let's start"))
    
#     response = await _call_llm_with_rate_limit_control(
#         [SystemMessage(content=prompt), *history],
#         state=state,
#     )
#     logger.debug(
#         "LLM reasoning completed",
#         extra=extra_(
#             run_id=state.get("run_id"),
#             ticket_id=state.get("ticket", {}).get("ticket_id"),
#             tool_calls_planned=len(response.tool_calls or []),
#         ),
#     )

#     planned = [
#         {"name": c.get("name"), "args": c.get("args")}
#         for c in (response.tool_calls or [])
#     ]
#     thought = (
#         f"Planned tool calls: {planned}"
#         if planned
#         else (response.content or "No tool calls; final response.")
#     )

#     # Create a step row for this reasoning decision.
#     step_number = int(state.get("total_step") or 0) + 1
#     step_id: str | None = None

#     def _op(session: Session) -> str:
#         return AgentStepRepo(session).log_step(
#             run_id=state["run_id"],
#             step_number=step_number,
#             thought=thought,
#             action="reasoning",
#             input_payload={"prompt": prompt},
#             output_payload={"tool_calls": planned, "content": response.content},
#             status="success",
#         )

#     try:
#         step_id = await _run_sync_with_pg(_op)
#     except Exception:
#         # Audit failures should never crash the agent.
#         logger.exception(
#             "Failed to write reasoning step audit",
#             extra=extra_(
#                 run_id=state.get("run_id"),
#                 ticket_id=state.get("ticket", {}).get("ticket_id"),
#             ),
#         )

#     return {
#         "messages": [response],
#         "total_step": step_number,
#         "current_step_id": step_id,
#     }


# async def tool_node(state: TicketAgentState) -> TicketAgentState:
#     outputs: list[ToolMessage] = []

#     current_step_id = state.get("current_step_id")
#     tool_calls_made = int(state.get("tool_calls_made") or 0)
#     injected_already = bool(state.get("_fault_injected") or False)

#     cfg = {
#         "configurable": {
#             "thread_id": state.get("thread_id"),
#             "run_id": state.get("run_id"),
#         }
#     }

#     for tool_call in state["messages"][-1].tool_calls:
#         name = tool_call["name"]
#         args = tool_call.get("args") or {}
#         tool_calls_made += 1
#         logger.debug(
#             "Tool call requested",
#             extra=extra_(
#                 run_id=state.get("run_id"),
#                 ticket_id=state.get("ticket", {}).get("ticket_id"),
#                 tool_name=name,
#                 attempt_max=envs.AGENT_MAX_RETRIES,
#             ),
#         )

#         # Retry budget with exponential backoff.
#         last_err: str | None = None
#         result: dict[str, Any] | None = None

#         last_exc: Exception | None = None
#         for attempt in range(envs.AGENT_MAX_RETRIES + 1):
#             try:
#                 # Force one realistic failure per ticket run to prove recovery.
#                 if envs.AGENT_FAULT_INJECTION and not injected_already and (
#                     name not in [
#                         'get_customer', 
#                         'get_product', 
#                         'get_order', 
#                         'check_refund_eligibility',
#                         'issue_refund',
#                         'escalate',
#                         'send_reply'
#                     ]
#                 ):
#                     injected_already, injected_result, injected_error = (
#                         _fault_injection_result()
#                     )
#                     if injected_error is not None:
#                         raise injected_error
#                     result = injected_result
#                     break

#                 tool = ticket_agent_tools_mapper[name]
#                 result = await tool.ainvoke(args, config=cfg)
#                 break
#             except Exception as e:
#                 last_exc = e
#                 last_err = f"{type(e).__name__}: {e}"
#                 logger.warning(
#                     "Tool call attempt failed",
#                     extra=extra_(
#                         run_id=state.get("run_id"),
#                         ticket_id=state.get("ticket", {}).get("ticket_id"),
#                         tool_name=name,
#                         attempt=attempt,
#                         error_type=type(e).__name__,
#                     ),
#                 )
#                 if attempt >= envs.AGENT_MAX_RETRIES:
#                     result = {"error": last_err}
#                     break
#                 await asyncio.sleep(min(0.5 * (2**attempt), 3.0))

#         if isinstance(result, dict) and result.get("malformed") is True:
#             status = "malformed"
#         elif isinstance(last_exc, TimeoutError):
#             status = "timeout"
#         else:
#             status = "success" if isinstance(result, dict) and "error" not in result else "failed"
#         error = result.get("error") if isinstance(result, dict) else None

#         # Persist tool execution audit linked to the reasoning step.
#         if current_step_id:
#             def _op(session: Session) -> None:
#                 ToolExecutionRepo(session).log_tool_call(
#                     step_id=current_step_id,
#                     tool_name=name,
#                     request=args,
#                     response=result if isinstance(result, dict) else {"result": result},
#                     status=status,
#                     error=error,
#                 )

#             try:
#                 await _run_sync_with_pg(_op)
#             except Exception:
#                 logger.exception(
#                     "Failed to write tool execution audit",
#                     extra=extra_(
#                         run_id=state.get("run_id"),
#                         ticket_id=state.get("ticket", {}).get("ticket_id"),
#                         tool_name=name,
#                     ),
#                 )

#         logger.info(
#             "Tool call completed",
#             extra=extra_(
#                 run_id=state.get("run_id"),
#                 ticket_id=state.get("ticket", {}).get("ticket_id"),
#                 tool_name=name,
#                 tool_status=status,
#             ),
#         )

#         outputs.append(
#             ToolMessage(
#                 content=_json_dumps(result),
#                 name=name,
#                 tool_call_id=tool_call["id"],
#             )
#         )

#     return {
#         "messages": outputs,
#         "tool_calls_made": tool_calls_made,
#         "_fault_injected": injected_already,
#     }



import asyncio
import json
import logging
import random
import time
from typing import Any

from aiolimiter import AsyncLimiter
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

# -----------------------------
# LLM + GLOBAL CONTROLS
# -----------------------------

_base_llm = get_chat_llm(envs.LLM_PROVIDER, envs.LLM_MODEL)
llm = _base_llm.bind_tools(ticket_agent_tools)

# Concurrency (parallel tickets allowed)
_llm_semaphore = asyncio.Semaphore(max(1, int(envs.AGENT_LLM_MAX_CONCURRENCY)))

# 🔥 TRUE RATE LIMITER (fixes Groq 30 RPM issue)
_llm_rate_limiter = AsyncLimiter(28, 60)  # keep buffer under 30 RPM

# Adaptive cooldown
_rate_limit_lock = asyncio.Lock()
_rate_limited_until_monotonic: float = 0.0


# -----------------------------
# HELPERS
# -----------------------------

async def _run_sync_with_pg(op):
    async for async_session in get_pgdb():
        return await async_session.run_sync(op)
    raise RuntimeError("Unable to acquire database session")


def _json_dumps(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=True, default=str)
    except Exception:
        return json.dumps(str(value), ensure_ascii=True)


def _fault_injection_result():
    mode = random.choice(["timeout", "malformed"])
    if mode == "timeout":
        return True, None, TimeoutError("Simulated tool timeout")
    return True, {"malformed": True, "raw": "<<<garbage>>>"}, None


def _is_rate_limit_error(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    return (
        "429" in text
        or "too many request" in text
        or "too many requests" in text
        or "rate limit" in text
    )


# -----------------------------
# LLM CALL WITH CONTROL
# -----------------------------

async def _call_llm_with_rate_limit_control(messages, state: TicketAgentState):
    global _rate_limited_until_monotonic

    provider = (envs.LLM_PROVIDER or "").lower()
    max_retries = int(envs.AGENT_LLM_MAX_RETRIES)
    min_delay = float(envs.AGENT_LLM_MIN_DELAY_SECONDS)
    max_delay = float(envs.AGENT_LLM_MAX_DELAY_SECONDS)
    max_backoff = float(envs.AGENT_LLM_BACKOFF_MAX_SECONDS)

    last_exc = None

    for attempt in range(max_retries + 1):

        # Adaptive cooldown (shared across all tasks)
        while True:
            async with _rate_limit_lock:
                wait_for = _rate_limited_until_monotonic - time.monotonic()

            if wait_for <= 0:
                break

            logger.warning(
                "Cooling down due to rate limit",
                extra=extra_(
                    run_id=state.get("run_id"),
                    wait_seconds=round(wait_for, 2),
                ),
            )

            await asyncio.sleep(min(wait_for, 3))  # 🔥 FIXED (no 60s blocking)

        try:
            # 🔥 KEY: Rate limiter ensures smooth distribution
            async with _llm_rate_limiter:
                async with _llm_semaphore:

                    # Small jitter only (avoid sync bursts)
                    if provider == "groq":
                        delay = random.uniform(min_delay, max_delay)
                        if delay > 0:
                            await asyncio.sleep(delay)

                    return await llm.ainvoke(messages)

        except Exception as exc:
            last_exc = exc

            if not _is_rate_limit_error(exc) or attempt >= max_retries:
                raise

            # Exponential backoff
            backoff = min((2**attempt) + random.uniform(0.2, 1.0), max_backoff)

            async with _rate_limit_lock:
                _rate_limited_until_monotonic = max(
                    _rate_limited_until_monotonic,
                    time.monotonic() + backoff,
                )

            logger.warning(
                "Rate limited, retrying",
                extra=extra_(
                    run_id=state.get("run_id"),
                    attempt=attempt,
                    sleep=round(backoff, 2),
                ),
            )

            await asyncio.sleep(backoff)

    raise last_exc or RuntimeError("LLM failed")


# -----------------------------
# REASONING NODE
# -----------------------------

async def reasoning_node(state: TicketAgentState) -> TicketAgentState:
    tool_calls_made = int(state.get("tool_calls_made") or 0)

    prompt = TICKET_AGENT_SYSTEM_PROMPT.render(
        ticket=state["ticket"],
        tool_calls_made=tool_calls_made,
    )

    history = list(state.get("messages") or [])

    if not history:
        history.append(HumanMessage(content="Let's start"))

    response = await _call_llm_with_rate_limit_control(
        [SystemMessage(content=prompt), *history],
        state=state,
    )

    planned = [
        {"name": c.get("name"), "args": c.get("args")}
        for c in (response.tool_calls or [])
    ]

    thought = (
        f"Planned tool calls: {planned}"
        if planned
        else (response.content or "No tool calls")
    )

    step_number = int(state.get("total_step") or 0) + 1
    step_id = None

    def _op(session: Session):
        return AgentStepRepo(session).log_step(
            run_id=state["run_id"],
            step_number=step_number,
            thought=thought,
            action="reasoning",
            input_payload={"prompt": prompt},
            output_payload={"tool_calls": planned},
            status="success",
        )

    try:
        step_id = await _run_sync_with_pg(_op)
    except Exception:
        logger.exception("Audit write failed")

    return {
        "messages": [response],
        "total_step": step_number,
        "current_step_id": step_id,
    }


# -----------------------------
# TOOL NODE
# -----------------------------

async def tool_node(state: TicketAgentState) -> TicketAgentState:
    outputs = []

    current_step_id = state.get("current_step_id")
    tool_calls_made = int(state.get("tool_calls_made") or 0)
    injected = state.get("_fault_injected", False)

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
        result = None
        last_exc = None

        for attempt in range(envs.AGENT_MAX_RETRIES + 1):
            try:
                if envs.AGENT_FAULT_INJECTION and not injected:
                    injected, result, err = _fault_injection_result()
                    if err:
                        raise err
                    break

                tool = ticket_agent_tools_mapper[name]
                result = await tool.ainvoke(args, config=cfg)
                break

            except Exception as e:
                last_exc = e
                if attempt >= envs.AGENT_MAX_RETRIES:
                    result = {"error": str(e)}
                    break
                await asyncio.sleep(min(0.5 * (2**attempt), 3))

        if current_step_id:
            def _op(session: Session):
                ToolExecutionRepo(session).log_tool_call(
                    step_id=current_step_id,
                    tool_name=name,
                    request=args,
                    response=result,
                    status="success" if "error" not in result else "failed",
                )

            try:
                await _run_sync_with_pg(_op)
            except Exception:
                logger.exception("Tool audit failed")

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
        "_fault_injected": injected,
    }