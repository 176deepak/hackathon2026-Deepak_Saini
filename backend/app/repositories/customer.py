from typing import Optional

import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
from app.models.models import Customer
from app.repositories.base import BaseCustomerRepo
from app.schemas.repo import CustomerOut

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.DB,
        "category": LogCategory.DATABASE,
        "component": __name__,
    },
)


def _to_customer_out(customer: Customer) -> CustomerOut:
    return CustomerOut(
        id=str(customer.id),
        email=customer.email,
        name=customer.name,
        tier=customer.tier.value if customer.tier else "",
    )


class CustomerRepo(BaseCustomerRepo):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_email(self, email: str) -> Optional[CustomerOut]:
        try:
            customer = self.db.scalar(select(Customer).where(Customer.email == email))
            if customer is None:
                logger.debug("Customer not found by email", extra=extra_(email=email))
                return None
            return _to_customer_out(customer)
        except Exception:
            logger.exception(
                "Failed to fetch customer by email", 
                extra=extra_(email=email)
            )
            raise

    def get_by_external_id(self, external_id: str) -> Optional[CustomerOut]:
        try:
            customer = self.db.scalar(
                select(Customer).where(Customer.external_customer_id == external_id)
            )
            if customer is None:
                logger.debug(
                    "Customer not found by external id",
                    extra=extra_(customer_external_id=external_id)
                )
                return None
            return _to_customer_out(customer)
        except Exception:
            logger.exception(
                "Failed to fetch customer by external id",
                extra=extra_(customer_external_id=external_id)
            )
            raise
