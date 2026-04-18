from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig


@tool("check_refund_eligibility", parse_docstring=True)
async def check_refund_eligibility(order_id: str, config: RunnableConfig) -> dict:
    """Check whether an order is eligible for refund based on policies.

    This includes evaluating return window, warranty, customer tier,
    and product-specific rules.

    Args:
        order_id: Unique order identifier.

    Returns:
        dict: Eligibility result with reasoning.
            Example:
            {
                "eligible": true,
                "reason": "Within return window"
            }
    """
    pass


@tool("issue_refund", parse_docstring=True)
async def issue_refund(order_id: str, amount: float, config: RunnableConfig) -> dict:
    """Issue a refund for the given order.

    This action is irreversible and should only be performed after confirming eligibility.

    Args:
        order_id: Unique order identifier.
        amount: Refund amount to be issued.

    Returns:
        dict: Refund execution result.
            Example:
            {
                "status": "success",
                "message": "Refund processed successfully"
            }
    """
    pass


@tool("send_reply", parse_docstring=True)
async def send_reply(ticket_id: str, message: str, config: RunnableConfig) -> dict:
    """Send a response message to the customer for a specific ticket.

    Args:
        ticket_id: Unique ticket identifier.
        message: Message content to send to the customer.

    Returns:
        dict: Result of sending message.
            Example:
            {
                "status": "sent"
            }
    """
    pass


@tool("escalate", parse_docstring=True)
async def escalate(
    ticket_id: str,
    summary: str,
    priority: str,
    config: RunnableConfig
) -> dict:
    """Escalate the ticket to a human support agent.

    This should be used when the agent is uncertain, lacks required information,
    or cannot safely resolve the issue.

    Args:
        ticket_id: Unique ticket identifier.
        summary: Structured summary of the issue and actions taken so far.
        priority: Priority level (low, medium, high, urgent).

    Returns:
        dict: Escalation result.
            Example:
            {
                "status": "escalated",
                "assigned_to": "human_agent"
            }
    """
    pass