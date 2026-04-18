from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.agents.handlers.tools import handle_get_order, handle_get_product


@tool("get_product", parse_docstring=True)
async def get_product(product_id: str, config: RunnableConfig) -> dict:
    """Fetch product details including return policy and warranty.

    Args:
        product_id: Unique product identifier.

    Returns:
        dict: Product metadata and policy details.
            Example:
            {
                "product_id": "P001",
                "name": "Headphones",
                "return_window_days": 30,
                "warranty_months": 12,
                "returnable": true
            }
    """
    _ = config
    return await handle_get_product(product_id=product_id)


@tool("get_order", parse_docstring=True)
async def get_order(order_id: str, config: RunnableConfig) -> dict:
    """Fetch order details including status, delivery, and refund info.

    Args:
        order_id: Unique order identifier.

    Returns:
        dict: Order details required for decision making.
            Example:
            {
                "order_id": "ORD-1001",
                "customer_id": "C001",
                "product_id": "P001",
                "status": "delivered",
                "return_deadline": "2024-03-15",
                "refund_status": null
            }
    """
    _ = config
    return await handle_get_order(order_id=order_id)
