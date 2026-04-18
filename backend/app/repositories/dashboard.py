import logging
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
from app.models.enums import TicketStatus
from app.models.models import Ticket
from app.repositories.base import BaseDashboardRepo
from app.schemas.repo import DashboardMetrics


class DashboardRepo(BaseDashboardRepo):
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

    def get_metrics(self) -> DashboardMetrics:
        try:
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

            self._logger.debug(
                "Dashboard metrics fetched",
                extra=extra_(
                    operation="repo_dashboard_metrics",
                    status="success",
                    total_tickets=total_tickets,
                    resolved=resolved,
                    escalated=escalated,
                    failed=failed,
                ),
            )

            return DashboardMetrics(
                total_tickets=total_tickets,
                resolved=resolved,
                escalated=escalated,
                failed=failed,
            )
        except Exception:
            self._logger.exception(
                "Failed to fetch dashboard metrics",
                extra=extra_(operation="repo_dashboard_metrics", status="failure"),
            )
            raise

    def get_recent_activity(self, limit: int = 10) -> list[dict]:
        try:
            tickets = self.db.scalars(
                select(Ticket).order_by(Ticket.updated_at.desc()).limit(limit)
            ).all()
            self._logger.debug(
                "Dashboard recent activity fetched",
                extra=extra_(
                    operation="repo_dashboard_recent_activity",
                    status="success",
                    limit=limit,
                    count=len(tickets),
                ),
            )
            return [
                {
                    "ticket_id": ticket.external_ticket_id,
                    "status": ticket.status.value if ticket.status else "",
                    "subject": ticket.subject,
                    "updated_at": ticket.updated_at,
                }
                for ticket in tickets
            ]
        except Exception:
            self._logger.exception(
                "Failed to fetch recent activity",
                extra=extra_(
                    operation="repo_dashboard_recent_activity",
                    status="failure",
                    limit=limit,
                ),
            )
            raise
