import json
from app.agents.prompts import TICKET_AGENT_SYSTEM_PROMPT
from app.agents.schemas import TicketAgentState
from app.agents.utils.utils import get_chat_llm
from app.agents.schemas import TicketAgentState
from app.agents.tools.tool_registry import get_tool
from app.agents.schemas.state import AgentState


llm = get_chat_llm("openai", "gpt-4o-mini")


def ticket_agent_reasoning_node(state: TicketAgentState) -> TicketAgentState:
    messages = state["messages"]

    prompt = TICKET_AGENT_SYSTEM_PROMPT + "\n\nUser:\n" + state["user_input"]

    response = llm.invoke(prompt)

    try:
        parsed = json.loads(response.content)
    except Exception:
        parsed = {
            "thought": "Failed to parse",
            "action": "escalate",
            "action_input": {}
        }

    state["tool_calls"].append(parsed)
    state["current_step"] += 1

    return state


def tool_node(state: TicketAgentState) -> TicketAgentState:
    last_call = state["tool_calls"][-1]

    tool_name = last_call["action"]
    tool_input = last_call.get("action_input", {})

    tool = get_tool(tool_name)

    if not tool:
        result = {"error": "Tool not found"}
    else:
        try:
            result = tool(tool_input)
        except Exception as e:
            result = {"error": str(e)}

    state["messages"].append({
        "role": "tool",
        "name": tool_name,
        "content": str(result)
    })

    return state


def decision_node(state: AgentState) -> str:
    last_call = state["tool_calls"][-1]

    if last_call["action"] in ["send_reply", "issue_refund", "escalate"]:
        return "end"

    if state["current_step"] > 6:
        return "end"

    return "continue"
