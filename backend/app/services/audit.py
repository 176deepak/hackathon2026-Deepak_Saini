import logging
from app.repositories.agent import AgentRunRepo
from app.services.base import BaseService
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.SERVICE,
        "category": LogCategory.API,
        "component": __name__,
    },
)


class AuditService(BaseService):
    def __init__(self, agent_run_repo: AgentRunRepo):
        super().__init__(agent_run_repo=agent_run_repo)

    def get_audit_timeline(self, ticket_id: str) -> dict | None:
        normalized_ticket_id = self._safe_str(ticket_id)
        self._validate_non_empty(normalized_ticket_id, "ticket_id")
        try:
            timeline = self.agent_run_repo.get_audit_timeline(normalized_ticket_id)
            logger.debug(
                "Audit timeline fetched",
                extra=extra_(
                    operation="svc_audit_timeline",
                    status="success" if timeline else "skipped",
                    ticket_id=normalized_ticket_id,
                ),
            )
            return timeline
        except Exception:
            logger.exception(
                "Failed to fetch audit timeline",
                extra=extra_(
                    operation="svc_audit_timeline",
                    status="failure",
                    ticket_id=normalized_ticket_id,
                ),
            )
            raise
