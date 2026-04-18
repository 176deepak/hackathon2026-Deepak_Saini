from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import TicketStatus
from app.models.models import Ticket, Escalation, Refund
from app.repositories.base import BaseTicketRepo, BaseEscalationRepo, BaseRefundRepo
from app.schemas.repo import TicketOut


def _to_ticket_out(ticket: Ticket) -> TicketOut:
    return TicketOut(
        id=str(ticket.id),
        external_ticket_id=ticket.external_ticket_id,
        customer_email=ticket.customer_email,
        subject=ticket.subject,
        body=ticket.body,
        status=ticket.status.value if ticket.status else "",
    )


class TicketRepo(BaseTicketRepo):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_id(self, ticket_id: str) -> Optional[TicketOut]:
        try:
            ticket_uuid = UUID(ticket_id)
        except ValueError:
            return None

        ticket = self.db.scalar(select(Ticket).where(Ticket.id == ticket_uuid))
        if ticket is None:
            return None
        return _to_ticket_out(ticket)

    def get_all_pending(self) -> list[TicketOut]:
        tickets = self.db.scalars(
            select(Ticket).where(Ticket.status == TicketStatus.PENDING)
        ).all()
        return [_to_ticket_out(ticket) for ticket in tickets]

    def update_status(self, ticket_id: str, status: str) -> None:
        try:
            ticket_uuid = UUID(ticket_id)
        except ValueError:
            return

        ticket = self.db.scalar(select(Ticket).where(Ticket.id == ticket_uuid))
        if ticket is None:
            return

        ticket.status = TicketStatus(status)
        self.db.add(ticket)
        self.db.commit()


class EscalationRepo(BaseEscalationRepo):
    def __init__(self, db: Session):
        super().__init__(db)

    def create_escalation(
        self, ticket_id: str, run_id: str, reason: str, summary: str, priority: str
    ) -> None:
        escalation = Escalation(
            ticket_id=UUID(ticket_id),
            agent_run_id=UUID(run_id),
            reason=reason,
            summary=summary,
            priority=priority,
        )
        self.db.add(escalation)
        self.db.commit()


class RefundRepo(BaseRefundRepo):
    def __init__(self, db: Session):
        super().__init__(db)

    def create_refund(
        self, order_id: str, amount: float, reason: str, initiated_by: str
    ) -> None:
        refund = Refund(
            order_id=UUID(order_id),
            amount=amount,
            reason=reason,
            initiated_by=initiated_by,
            status="pending",
            created_at=datetime.utcnow(),
        )
        self.db.add(refund)
        self.db.commit()
