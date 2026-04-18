from typing import Optional

import logging
from app.repositories.base import BaseCustomerRepo
from app.schemas.repo import CustomerOut
from app.services.base import BaseCustomerService
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.SERVICE,
        "category": LogCategory.API,
        "component": __name__,
    },
)


class CustomerService(BaseCustomerService):
    def __init__(self, customer_repo: BaseCustomerRepo):
        super().__init__(customer_repo=customer_repo)

    def get_customer(self, email: str) -> Optional[CustomerOut]:
        normalized_email = self._safe_str(email)
        self._validate_non_empty(normalized_email, "email")
        try:
            customer = self.customer_repo.get_by_email(normalized_email)
            logger.debug("Customer fetched", extra=extra_(email=normalized_email))
            return customer
        except Exception:
            logger.exception(
                "Failed to fetch customer",
                extra=extra_(email=normalized_email),
            )
            raise

    def get_customer_by_id(self, customer_id: str) -> Optional[CustomerOut]:
        normalized_customer_id = self._safe_str(customer_id)
        self._validate_non_empty(normalized_customer_id, "customer_id")
        try:
            customer = self.customer_repo.get_by_external_id(normalized_customer_id)
            logger.debug(
                "Customer fetched by id",
                extra=extra_(customer_id=normalized_customer_id),
            )
            return customer
        except Exception:
            logger.exception(
                "Failed to fetch customer by id",
                extra=extra_(customer_id=normalized_customer_id),
            )
            raise
