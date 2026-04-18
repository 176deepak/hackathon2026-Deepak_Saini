from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.agents.handlers.tools import (
    handle_check_refund_eligibility,
    handle_escalate,
    handle_issue_refund,
    handle_send_reply,
)


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
    _ = config
    return await handle_check_refund_eligibility(order_id=order_id)


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
    _ = config
    return await handle_issue_refund(order_id=order_id, amount=amount)


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
    _ = config
    return await handle_send_reply(ticket_id=ticket_id, message=message)


def _extract_run_id(config: RunnableConfig) -> str | None:
    cfg = config if isinstance(config, dict) else {}

    # LangChain usually stores custom values in configurable
    configurable: Any = cfg.get("configurable", {})
    if isinstance(configurable, dict):
        run_id = configurable.get("run_id")
        if run_id:
            return str(run_id)

    run_id = cfg.get("run_id")
    if run_id:
        return str(run_id)

    return None


@tool("escalate", parse_docstring=True)
async def escalate(
    ticket_id: str,
    summary: str,
    priority: str,
    config: RunnableConfig,
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
    run_id = _extract_run_id(config)
    return await handle_escalate(
        ticket_id=ticket_id,
        summary=summary,
        priority=priority,
        run_id=run_id,
    )
