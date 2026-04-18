from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis import AsyncRedisSaver

from app.core.config import envs
from app.clients.redis import get_redis
from app.agents.schemas import TicketAgentState
from app.agents.nodes.ticket_agent import reasoning_node, tool_node
from app.agents.edges.ticket_agent import should_continue


async def init_ticket_resolver_agent():
    ttl_config = {
        "default_ttl": envs.HISTORY_TTL,
        "refresh_on_read": envs.HISTORY_TTL_REFRESH_ON_READ,
    }

    # Redis-backed checkpointing (session storage)
    checkpointer = AsyncRedisSaver(redis_client=get_redis(), ttl=ttl_config)
    await checkpointer.asetup()

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
    graph = workflow.compile(checkpointer=checkpointer)
    if envs.AGENT_DRAW_GRAPH:
        graph.get_graph().draw_mermaid_png(output_file_path="ticket_resolver.png")
    return graph
