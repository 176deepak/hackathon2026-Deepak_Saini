from app.agents.schemas import TicketAgentState
import logging
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.AGENT,
        "category": LogCategory.AGENT,
        "component": __name__,
    },
)


def should_continue(state: TicketAgentState):
    messages = state["messages"]

    # If the last message is not a tool call, then finish
    if not messages[-1].tool_calls:
        logger.debug(
            "Agent decided to end (no tool calls)",
            extra=extra_(
                run_id=state.get("run_id"),
                ticket_id=state.get("ticket", {}).get("ticket_id"),
            ),
        )
        return "end"

    # default to continue
    logger.debug(
        "Agent decided to continue (tool calls present)",
        extra=extra_(
            run_id=state.get("run_id"),
            ticket_id=state.get("ticket", {}).get("ticket_id"),
            tool_calls=len(messages[-1].tool_calls or []),
        ),
    )
    return "continue"
