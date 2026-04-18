from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import TicketStatus
from app.models.models import Ticket
from app.repositories.base import BaseDashboardRepo
from app.schemas.repo import DashboardMetrics


class DashboardRepo(BaseDashboardRepo):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_metrics(self) -> DashboardMetrics:
        total_tickets = self.db.scalar(select(func.count()).select_from(Ticket)) or 0
        resolved = self.db.scalar(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.status == TicketStatus.RESOLVED)
        ) or 0
        escalated = self.db.scalar(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.status == TicketStatus.ESCALATED)
        ) or 0
        failed = self.db.scalar(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.status == TicketStatus.FAILED)
        ) or 0

        return DashboardMetrics(
            total_tickets=total_tickets,
            resolved=resolved,
            escalated=escalated,
            failed=failed,
        )

    def get_recent_activity(self, limit: int = 10) -> list[dict]:
        tickets = self.db.scalars(
            select(Ticket).order_by(Ticket.updated_at.desc()).limit(limit)
        ).all()
        return [
            {
                "ticket_id": ticket.external_ticket_id,
                "status": ticket.status.value if ticket.status else "",
                "subject": ticket.subject,
                "updated_at": ticket.updated_at,
            }
            for ticket in tickets
        ]
