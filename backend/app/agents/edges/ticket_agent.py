from app.agents.schemas import TicketAgentState


def should_continue(state: TicketAgentState):
    messages = state["messages"]

    # If the last message is not a tool call, then finish
    if not messages[-1].tool_calls:
        return "end"

    # default to continue
    return "continue"