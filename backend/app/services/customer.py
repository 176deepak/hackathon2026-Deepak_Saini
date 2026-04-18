from typing import Optional

from app.repositories.base import BaseCustomerRepo
from app.schemas.repo import CustomerOut
from app.services.base import BaseCustomerService


class CustomerService(BaseCustomerService):
    def __init__(self, customer_repo: BaseCustomerRepo):
        super().__init__(customer_repo=customer_repo)

    def get_customer(self, email: str) -> Optional[CustomerOut]:
        normalized_email = self._safe_str(email)
        self._validate_non_empty(normalized_email, "email")
        return self.customer_repo.get_by_email(normalized_email)

    def get_customer_by_id(self, customer_id: str) -> Optional[CustomerOut]:
        normalized_customer_id = self._safe_str(customer_id)
        self._validate_non_empty(normalized_customer_id, "customer_id")
        return self.customer_repo.get_by_external_id(normalized_customer_id)
