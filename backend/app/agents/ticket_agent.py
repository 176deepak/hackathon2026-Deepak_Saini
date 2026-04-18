from langgraph.graph import StateGraph, END

from app.agents.schemas.state import AgentState
from app.agents.nodes.reasoning_node import reasoning_node
from app.agents.nodes.tool_node import tool_node
from app.agents.nodes.decision_node import decision_node


def build_agent():
    graph = StateGraph(AgentState)

    graph.add_node("reason", reasoning_node)
    graph.add_node("tool", tool_node)

    graph.set_entry_point("reason")

    graph.add_edge("reason", "tool")

    graph.add_conditional_edges(
        "tool",
        decision_node,
        {
            "continue": "reason",
            "end": END
        }
    )

    return graph.compile()