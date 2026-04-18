from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
from app.models.enums import TicketStatus
from app.models.models import Ticket, Escalation, Refund, TicketMessage
from app.repositories.base import BaseTicketRepo, BaseEscalationRepo, BaseRefundRepo
from app.schemas.repo import TicketOut
import logging


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
        self._logger = AppLoggerAdapter(
            logging.getLogger(__name__),
            {
                "layer": LogLayer.DB,
                "category": LogCategory.DATABASE,
                "component": self.__class__.__name__,
            },
        )

    def get_by_id(self, ticket_id: str) -> Optional[TicketOut]:
        try:
            ticket_uuid = UUID(ticket_id)
        except ValueError:
            return None

        ticket = self.db.scalar(select(Ticket).where(Ticket.id == ticket_uuid))
        if ticket is None:
            return None
        return _to_ticket_out(ticket)

    def get_by_external_id(self, external_ticket_id: str) -> Optional[TicketOut]:
        ticket = self.db.scalar(
            select(Ticket).where(Ticket.external_ticket_id == external_ticket_id)
        )
        if ticket is None:
            return None
        return _to_ticket_out(ticket)

    def get_by_reference(self, ticket_ref: str) -> Optional[TicketOut]:
        ticket_by_id = self.get_by_id(ticket_ref)
        if ticket_by_id is not None:
            return ticket_by_id
        return self.get_by_external_id(ticket_ref.strip())

    def get_all_pending(self) -> list[TicketOut]:
        tickets = self.db.scalars(
            select(Ticket).where(Ticket.status == TicketStatus.PENDING)
        ).all()
        return [_to_ticket_out(ticket) for ticket in tickets]

    def claim_pending(self, limit: int = 20) -> list[TicketOut]:
        """Atomically claim pending tickets by marking them as processing.

        Uses SELECT ... FOR UPDATE SKIP LOCKED to support safe concurrency if multiple
        runners are active.
        """
        stmt = (
            select(Ticket)
            .where(Ticket.status == TicketStatus.PENDING)
            .order_by(Ticket.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
        rows = self.db.scalars(stmt).all()
        self._logger.debug(
            "Claiming pending tickets",
            extra=extra_(
                operation="claim_pending",
                status="start",
                limit=limit,
                found=len(rows),
            ),
        )
        try:
            for t in rows:
                t.status = TicketStatus.PROCESSING
                self.db.add(t)
            self.db.commit()
        except Exception:
            self._logger.exception(
                "Failed to claim pending tickets",
                extra=extra_(
                    operation="claim_pending",
                    status="failure",
                    limit=limit,
                    found=len(rows),
                ),
            )
            self.db.rollback()
            raise
        return [_to_ticket_out(t) for t in rows]

    def list_tickets(
        self,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TicketOut]:
        stmt = select(Ticket).order_by(Ticket.created_at.desc())
        if status:
            stmt = stmt.where(Ticket.status == TicketStatus(status))

        tickets = self.db.scalars(stmt.offset(offset).limit(limit)).all()
        return [_to_ticket_out(ticket) for ticket in tickets]

    def count_tickets(self, status: str | None = None) -> int:
        stmt = select(func.count()).select_from(Ticket)
        if status:
            stmt = stmt.where(Ticket.status == TicketStatus(status))
        return self.db.scalar(stmt) or 0

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

    def create_message(
        self,
        ticket_ref: str,
        sender_type: str,
        message: str,
    ) -> bool:
        ticket = self.db.scalar(
            select(Ticket).where(Ticket.external_ticket_id == ticket_ref.strip())
        )
        if ticket is None:
            try:
                ticket_uuid = UUID(ticket_ref)
            except ValueError:
                return False
            ticket = self.db.scalar(select(Ticket).where(Ticket.id == ticket_uuid))
            if ticket is None:
                return False

        ticket_message = TicketMessage(
            ticket_id=ticket.id,
            sender_type=sender_type,
            message=message,
        )
        self.db.add(ticket_message)
        self.db.commit()
        return True


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
