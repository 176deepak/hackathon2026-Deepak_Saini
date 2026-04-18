from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis import AsyncRedisSaver

import logging
from app.core.config import envs
from app.clients.redis import get_redis
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
from app.agents.schemas import TicketAgentState
from app.agents.nodes.ticket_agent import reasoning_node, tool_node
from app.agents.edges.ticket_agent import should_continue

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.AGENT,
        "category": LogCategory.AGENT,
        "component": __name__,
    },
)


async def init_ticket_resolver_agent():
    ttl_config = {
        "default_ttl": envs.HISTORY_TTL,
        "refresh_on_read": envs.HISTORY_TTL_REFRESH_ON_READ,
    }

    # Redis-backed checkpointing (session storage)
    try:
        logger.info(
            "Initializing Redis checkpointer for LangGraph",
            extra=extra_(
                history_ttl=envs.HISTORY_TTL,
                refresh_on_read=envs.HISTORY_TTL_REFRESH_ON_READ,
            ),
        )
        checkpointer = AsyncRedisSaver(redis_client=get_redis(), ttl=ttl_config)
        await checkpointer.asetup()
    except Exception:
        logger.exception("Failed to initialize LangGraph Redis checkpointer")
        raise

    workflow = StateGraph(TicketAgentState)

    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("tools",  tool_node)
    workflow.set_entry_point("reasoning")
    workflow.add_conditional_edges(
        "reasoning",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )
    workflow.add_edge("tools", "reasoning")
    try:
        graph = workflow.compile(checkpointer=checkpointer)
        logger.info("Agent graph compiled")
        if envs.AGENT_DRAW_GRAPH:
            graph.get_graph().draw_mermaid_png(output_file_path="ticket_resolver.png")
            logger.debug("Agent graph diagram written")
        return graph
    except Exception:
        logger.exception("Failed to compile agent graph")
        raise
