from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import OrderStatus, RefundStatus
from app.models.models import Order
from app.repositories.base import BaseOrderRepo
from app.schemas.repo import OrderOut


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
        order = self.db.scalar(select(Order).where(Order.external_order_id == order_id))
        if order is None:
            return None
        return _to_order_out(order)

    def get_by_customer(self, customer_id: str) -> list[OrderOut]:
        try:
            customer_uuid = UUID(customer_id)
        except ValueError:
            return []

        orders = self.db.scalars(
            select(Order).where(Order.customer_id == customer_uuid)
        ).all()
        return [_to_order_out(order) for order in orders]

    def update_status(self, order_id: str, status: str) -> None:
        order = self.db.scalar(select(Order).where(Order.external_order_id == order_id))
        if order is None:
            return

        order.status = OrderStatus(status)
        self.db.add(order)
        self.db.commit()

    def update_refund_status(self, order_id: str, status: str) -> None:
        order = self.db.scalar(select(Order).where(Order.external_order_id == order_id))
        if order is None:
            return

        order.refund_status = RefundStatus(status)
        self.db.add(order)
        self.db.commit()
