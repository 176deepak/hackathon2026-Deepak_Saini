from typing import Optional

from app.models.enums import OrderStatus, RefundStatus
from app.repositories.base import BaseOrderRepo
from app.schemas.repo import OrderOut
from app.services.base import BaseOrderService


class OrderService(BaseOrderService):
    def __init__(self, order_repo: BaseOrderRepo):
        super().__init__(order_repo=order_repo)

    def get_order(self, order_id: str) -> Optional[OrderOut]:
        normalized_order_id = self._safe_str(order_id)
        self._validate_non_empty(normalized_order_id, "order_id")
        return self.order_repo.get_by_external_id(normalized_order_id)

    def get_orders_by_customer(self, customer_id: str) -> list[OrderOut]:
        normalized_customer_id = self._safe_str(customer_id)
        self._validate_non_empty(normalized_customer_id, "customer_id")
        return self.order_repo.get_by_customer(normalized_customer_id)

    def cancel_order(self, order_id: str) -> None:
        normalized_order_id = self._safe_str(order_id)
        self._validate_non_empty(normalized_order_id, "order_id")
        self.order_repo.update_status(normalized_order_id, OrderStatus.CANCELLED.value)

    def mark_refunded(self, order_id: str) -> None:
        normalized_order_id = self._safe_str(order_id)
        self._validate_non_empty(normalized_order_id, "order_id")
        self.order_repo.update_refund_status(
            normalized_order_id,
            RefundStatus.REFUNDED.value,
        )
