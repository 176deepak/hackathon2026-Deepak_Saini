from typing import Optional

import logging
from app.models.enums import TicketStatus
from app.repositories.base import BaseTicketRepo
from app.schemas.repo import TicketOut
from app.services.base import BaseTicketService
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.SERVICE,
        "category": LogCategory.API,
        "component": __name__,
    },
)


class TicketService(BaseTicketService):
    def __init__(self, ticket_repo: BaseTicketRepo):
        super().__init__(ticket_repo=ticket_repo)

    def get_ticket(self, ticket_id: str) -> Optional[TicketOut]:
        normalized_ticket_id = self._safe_str(ticket_id)
        self._validate_non_empty(normalized_ticket_id, "ticket_id")
        try:
            ticket = self.ticket_repo.get_by_id(normalized_ticket_id)
            logger.debug("Ticket fetched",extra=extra_(ticket_id=ticket_id))
            return ticket
        except Exception:
            logger.exception("Failed to fetch ticket",extra=extra_(ticket_id=ticket_id))
            raise

    def get_ticket_by_reference(self, ticket_ref: str) -> Optional[TicketOut]:
        normalized_ticket_ref = self._safe_str(ticket_ref)
        self._validate_non_empty(normalized_ticket_ref, "ticket_id")
        try:
            ticket = self.ticket_repo.get_by_reference(normalized_ticket_ref)
            logger.debug(
                "Ticket fetched by reference",
                extra=extra_(ticket_ref=ticket_ref),
            )
            return ticket
        except Exception:
            logger.exception(
                "Failed to fetch ticket by reference",
                extra=extra_(ticket_ref=ticket_ref),
            )
            raise

    def list_tickets(
        self,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
    ) -> tuple[list[TicketOut], int]:
        offset = (page - 1) * limit
        try:
            items = self.ticket_repo.list_tickets(
                status=status,
                offset=offset,
                limit=limit,
            )
            total = self.ticket_repo.count_tickets(status=status)
            logger.debug(
                "Tickets listed",
                extra=extra_(status_filter=status, page=page, limit=limit, total=total),
            )
            return items, total
        except Exception:
            logger.exception(
                "Failed to list tickets",
                extra=extra_(status_filter=status,page=page,limit=limit),
            )
            raise

    def get_pending_tickets(self) -> list[TicketOut]:
        return self.ticket_repo.get_all_pending()

    def update_status_by_reference(
        self,
        ticket_ref: str,
        status: str,
    ) -> Optional[TicketOut]:
        ticket = self.get_ticket_by_reference(ticket_ref)
        if ticket is None:
            logger.warning(
                "Ticket not found for status update",
                extra=extra_(ticket_ref=ticket_ref, new_status=status),
            )
            return None

        try:
            self.ticket_repo.update_status(ticket.id, status)
            logger.info(
                "Ticket status updated",
                extra=extra_(ticket_ref=ticket_ref, new_status=status),
            )
            return self.get_ticket_by_reference(ticket.id)
        except Exception:
            logger.exception(
                "Failed to update ticket status",
                extra=extra_(ticket_ref=ticket_ref, new_status=status),
            )
            raise

    def mark_processing(self, ticket_id: str) -> None:
        normalized_ticket_id = self._safe_str(ticket_id)
        self._validate_non_empty(normalized_ticket_id, "ticket_id")
        self.ticket_repo.update_status(
            normalized_ticket_id,
            TicketStatus.PROCESSING.value,
        )

    def mark_resolved(self, ticket_id: str) -> None:
        normalized_ticket_id = self._safe_str(ticket_id)
        self._validate_non_empty(normalized_ticket_id, "ticket_id")
        self.ticket_repo.update_status(normalized_ticket_id, TicketStatus.RESOLVED.value)

    def mark_escalated(self, ticket_id: str) -> None:
        normalized_ticket_id = self._safe_str(ticket_id)
        self._validate_non_empty(normalized_ticket_id, "ticket_id")
        self.ticket_repo.update_status(
            normalized_ticket_id,
            TicketStatus.ESCALATED.value,
        )

    def mark_failed(self, ticket_id: str) -> None:
        normalized_ticket_id = self._safe_str(ticket_id)
        self._validate_non_empty(normalized_ticket_id, "ticket_id")
        self.ticket_repo.update_status(normalized_ticket_id, TicketStatus.FAILED.value)
