from langchain_core.messages import ToolMessage
from app.agents.prompts import TICKET_AGENT_SYSTEM_PROMPT
from app.agents.schemas import TicketAgentState
from app.agents.utils.utils import get_chat_llm
from app.agents.tools.registry import ticket_agent_tools, ticket_agent_tools_mapper


llm = get_chat_llm("openai", "gpt-4o-mini")
llm.bind_tools(ticket_agent_tools)


async def reasoning_node(state: TicketAgentState) -> TicketAgentState:
    prompt = TICKET_AGENT_SYSTEM_PROMPT.render(**state["ticket"])
    response = await llm.ainvoke(prompt)
    return {"messages": [response]}


def tool_node(state: TicketAgentState) -> TicketAgentState:
    outputs = []

    for tool_call in state["messages"][-1].tool_calls:

        tool_result = ticket_agent_tools_mapper[tool_call["name"]].invoke(
            tool_call["args"]
        )
        outputs.append(
            ToolMessage(
                content=tool_result,
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": outputs}