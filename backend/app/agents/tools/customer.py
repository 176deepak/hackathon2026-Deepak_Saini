from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig


@tool("get_customer", parse_docstring=True)
async def get_customer(
    customer_id: str | None,
    email: str | None,
    config: RunnableConfig
) -> dict:
    """Fetch customer details using either customer ID or email.

    At least one of customer_id or email must be provided.

    Args:
        customer_id: Unique customer identifier (optional if email is provided).
        email: Customer email address (optional if customer_id is provided).

    Returns:
        dict: Customer details including profile, tier, and history.
            Example:
            {
                "customer_id": "C001",
                "name": "Alice Turner",
                "tier": "vip",
                "total_orders": 47,
                "risk_flag": false
            }
    """
    pass