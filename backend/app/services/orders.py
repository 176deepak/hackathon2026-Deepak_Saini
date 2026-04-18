from typing import Optional

import logging
from app.models.enums import OrderStatus, RefundStatus
from app.repositories.base import BaseOrderRepo
from app.schemas.repo import OrderOut
from app.services.base import BaseOrderService
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.SERVICE,
        "category": LogCategory.API,
        "component": __name__,
    },
)


class OrderService(BaseOrderService):
    def __init__(self, order_repo: BaseOrderRepo):
        super().__init__(order_repo=order_repo)

    def get_order(self, order_id: str) -> Optional[OrderOut]:
        normalized_order_id = self._safe_str(order_id)
        self._validate_non_empty(normalized_order_id, "order_id")
        try:
            order = self.order_repo.get_by_external_id(normalized_order_id)
            logger.debug("Order fetched",extra=extra_(order_id=order_id))
            return order
        except Exception:
            logger.exception(
                "Failed to fetch order",
                extra=extra_(order_id=order_id),
            )
            raise

    def get_orders_by_customer(self, customer_id: str) -> list[OrderOut]:
        normalized_customer_id = self._safe_str(customer_id)
        self._validate_non_empty(normalized_customer_id, "customer_id")
        return self.order_repo.get_by_customer(normalized_customer_id)

    def cancel_order(self, order_id: str) -> None:
        normalized_order_id = self._safe_str(order_id)
        self._validate_non_empty(normalized_order_id, "order_id")
        try:
            self.order_repo.update_status(normalized_order_id, OrderStatus.CANCELLED.value)
            logger.info("Order cancelled", extra=extra_(order_id=order_id))
        except Exception:
            logger.exception(
                "Failed to cancel order",
                extra=extra_(order_id=order_id),
            )
            raise

    def mark_refunded(self, order_id: str) -> None:
        normalized_order_id = self._safe_str(order_id)
        self._validate_non_empty(normalized_order_id, "order_id")
        try:
            self.order_repo.update_refund_status(
                normalized_order_id,
                RefundStatus.REFUNDED.value,
            )
            logger.info(
                "Order marked refunded",
                extra=extra_(order_id=order_id),
            )
        except Exception:
            logger.exception(
                "Failed to mark order refunded",
                extra=extra_(order_id=order_id),
            )
            raise
