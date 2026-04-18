from typing import Optional

from app.models.enums import TicketStatus
from app.repositories.base import BaseTicketRepo
from app.schemas.repo import TicketOut
from app.services.base import BaseTicketService


class TicketService(BaseTicketService):
    def __init__(self, ticket_repo: BaseTicketRepo):
        super().__init__(ticket_repo=ticket_repo)

    def get_ticket(self, ticket_id: str) -> Optional[TicketOut]:
        normalized_ticket_id = self._safe_str(ticket_id)
        self._validate_non_empty(normalized_ticket_id, "ticket_id")
        return self.ticket_repo.get_by_id(normalized_ticket_id)

    def get_ticket_by_reference(self, ticket_ref: str) -> Optional[TicketOut]:
        normalized_ticket_ref = self._safe_str(ticket_ref)
        self._validate_non_empty(normalized_ticket_ref, "ticket_id")
        return self.ticket_repo.get_by_reference(normalized_ticket_ref)

    def list_tickets(
        self,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
    ) -> tuple[list[TicketOut], int]:
        offset = (page - 1) * limit
        items = self.ticket_repo.list_tickets(
            status=status,
            offset=offset,
            limit=limit,
        )
        total = self.ticket_repo.count_tickets(status=status)
        return items, total

    def get_pending_tickets(self) -> list[TicketOut]:
        return self.ticket_repo.get_all_pending()

    def update_status_by_reference(
        self,
        ticket_ref: str,
        status: str,
    ) -> Optional[TicketOut]:
        ticket = self.get_ticket_by_reference(ticket_ref)
        if ticket is None:
            return None

        self.ticket_repo.update_status(ticket.id, status)
        return self.get_ticket_by_reference(ticket.id)

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
