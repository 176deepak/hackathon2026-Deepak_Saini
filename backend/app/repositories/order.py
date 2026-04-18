from typing import Optional
from uuid import UUID

import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
from app.models.enums import OrderStatus, RefundStatus
from app.models.models import Order
from app.repositories.base import BaseOrderRepo
from app.schemas.repo import OrderOut


logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.DB,
        "category": LogCategory.DATABASE,
        "component": __name__,
    }
)


def _to_order_out(order: Order) -> OrderOut:
    return OrderOut(
        id=str(order.id),
        external_order_id=order.external_order_id,
        customer_id=str(order.customer_id),
        product_id=str(order.product_id),
        status=order.status.value if order.status else "",
        amount=order.amount or 0.0,
        return_deadline=order.return_deadline,
        refund_status=order.refund_status.value if order.refund_status else None,
        tracking_number=order.tracking_number,
    )


class OrderRepo(BaseOrderRepo):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_external_id(self, order_id: str) -> Optional[OrderOut]:
        try:
            order = self.db.scalar(
                select(Order).where(Order.external_order_id == order_id)
            )
            if order is None:
                logger.debug("Order not found", extra=extra_(order_id=order_id))
                return None
            return _to_order_out(order)
        except Exception:
            logger.exception("Failed to fetch order", extra=extra_(order_id=order_id))
            raise

    def get_by_customer(self, customer_id: str) -> list[OrderOut]:
        try:
            customer_uuid = UUID(customer_id)
        except ValueError:
            logger.warning(
                "Invalid customer UUID for order lookup",
                extra=extra_(customer_id=customer_id),
            )
            return []

        try:
            orders = self.db.scalars(
                select(Order).where(Order.customer_id == customer_uuid)
            ).all()
            logger.debug(
                "Orders fetched for customer",
                extra=extra_(customer_id=customer_id, count=len(orders)),
            )
            return [_to_order_out(order) for order in orders]
        except Exception:
            logger.exception(
                "Failed to fetch orders for customer",
                extra=extra_(customer_id=customer_id),
            )
            raise

    def update_status(self, order_id: str, status: str) -> None:
        try:
            order = self.db.scalar(
                select(Order).where(Order.external_order_id == order_id)
            )
            if order is None:
                logger.warning(
                    "Order not found for status update",
                    extra=extra_(order_id=order_id, new_status=status),
                )
                return

            order.status = OrderStatus(status)
            self.db.add(order)
            self.db.commit()
            logger.info(
                "Order status updated",
                extra=extra_(order_id=order_id, new_status=status),
            )
        except Exception:
            logger.exception(
                "Failed to update order status",
                extra=extra_(order_id=order_id,new_status=status),
            )
            self.db.rollback()
            raise

    def update_refund_status(self, order_id: str, status: str) -> None:
        try:
            order = self.db.scalar(
                select(Order).where(Order.external_order_id == order_id)
            )
            if order is None:
                logger.warning(
                    "Order not found for refund status update",
                    extra=extra_(order_id=order_id, new_status=status)
                )
                return

            order.refund_status = RefundStatus(status)
            self.db.add(order)
            self.db.commit()
            logger.info(
                "Order refund status updated",
                extra=extra_(order_id=order_id, new_status=status)
            )
        except Exception:
            logger.exception(
                "Failed to update refund status",
                extra=extra_(order_id=order_id, new_status=status)
            )
            self.db.rollback()
            raise
