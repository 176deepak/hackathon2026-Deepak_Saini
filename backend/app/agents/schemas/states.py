from typing import Annotated, Sequence, TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class Ticket(TypedDict):
    ticket_id: str
    customer_email: str
    subject: str
    body: str
    

class TicketAgentState(TypedDict):
    ticket: Ticket
    messages: Annotated[Sequence[BaseMessage], add_messages]
    total_step: int
    run_id: str
    current_step_id: str | None
    tool_calls_made: int
    final_response: Optional[str]
