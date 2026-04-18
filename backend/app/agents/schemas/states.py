from typing import TypedDict, List, Optional, Dict, Any
from langchain.messages import AnyMessage, ToolCall

class TicketAgentState(TypedDict):
    ticket_id: str
    user_input: str
    messages: List[AnyMessage]
    current_step: int
    tool_calls: List[ToolCall]
    final_response: Optional[str]
    status: str  # running, completed, failed, escalated