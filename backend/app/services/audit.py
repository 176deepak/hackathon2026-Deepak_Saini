from app.repositories.agent import AgentRunRepo
from app.services.base import BaseService


class AuditService(BaseService):
    def __init__(self, agent_run_repo: AgentRunRepo):
        super().__init__(agent_run_repo=agent_run_repo)

    def get_audit_timeline(self, ticket_id: str) -> dict | None:
        normalized_ticket_id = self._safe_str(ticket_id)
        self._validate_non_empty(normalized_ticket_id, "ticket_id")
        return self.agent_run_repo.get_audit_timeline(normalized_ticket_id)
