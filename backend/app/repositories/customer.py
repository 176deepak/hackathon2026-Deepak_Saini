from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import Customer
from app.repositories.base import BaseCustomerRepo
from app.schemas.repo import CustomerOut


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
        customer = self.db.scalar(select(Customer).where(Customer.email == email))
        if customer is None:
            return None
        return _to_customer_out(customer)

    def get_by_external_id(self, external_id: str) -> Optional[CustomerOut]:
        customer = self.db.scalar(
            select(Customer).where(Customer.external_customer_id == external_id)
        )
        if customer is None:
            return None
        return _to_customer_out(customer)
