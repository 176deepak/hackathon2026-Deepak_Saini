from typing import Annotated, Literal

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.pg import get_pgdb
from app.repositories.agent import AgentRunRepo
from app.repositories.dashboard import DashboardRepo
from app.repositories.ticket import TicketRepo
from app.services.audit import AuditService
from app.services.dashboard import DashboardService
from app.services.system import SystemService
from app.services.tickets import TicketService


TicketStatusFilter = Literal[
    "pending",
    "processing",
    "resolved",
    "escalated",
    "waiting_for_customer",
    "failed",
]


class TicketServiceExecutor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_tickets(
        self,
        page: int,
        limit: int,
        status: TicketStatusFilter | None,
    ):
        def _op(session):
            service = TicketService(ticket_repo=TicketRepo(db=session))
            return service.list_tickets(page=page, limit=limit, status=status)

        return await self.db.run_sync(_op)

    async def get_ticket_by_reference(self, ticket_id: str):
        def _op(session):
            service = TicketService(ticket_repo=TicketRepo(db=session))
            return service.get_ticket_by_reference(ticket_id)

        return await self.db.run_sync(_op)

    async def update_status_by_reference(self, ticket_id: str, status: str):
        def _op(session):
            service = TicketService(ticket_repo=TicketRepo(db=session))
            return service.update_status_by_reference(ticket_id, status)

        return await self.db.run_sync(_op)


class DashboardServiceExecutor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_metrics(self):
        def _op(session):
            service = DashboardService(dashboard_repo=DashboardRepo(db=session))
            return service.get_metrics()

        return await self.db.run_sync(_op)

    async def get_recent_activity(self, limit: int):
        def _op(session):
            service = DashboardService(dashboard_repo=DashboardRepo(db=session))
            return service.get_recent_activity(limit=limit)

        return await self.db.run_sync(_op)


class AuditServiceExecutor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_audit_timeline(self, ticket_id: str):
        def _op(session):
            service = AuditService(agent_run_repo=AgentRunRepo(db=session))
            return service.get_audit_timeline(ticket_id=ticket_id)

        return await self.db.run_sync(_op)


class SystemServiceExecutor:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.service = SystemService()

    async def check_health(self):
        return await self.db.run_sync(lambda session: self.service.check_health(db=session))

    async def ping(self):
        return self.service.ping()


async def get_ticket_service(
    db: AsyncSession = Depends(get_pgdb),
) -> TicketServiceExecutor:
    return TicketServiceExecutor(db=db)


async def get_dashboard_service(
    db: AsyncSession = Depends(get_pgdb),
) -> DashboardServiceExecutor:
    return DashboardServiceExecutor(db=db)


async def get_audit_service(
    db: AsyncSession = Depends(get_pgdb),
) -> AuditServiceExecutor:
    return AuditServiceExecutor(db=db)


async def get_system_service(
    db: AsyncSession = Depends(get_pgdb),
) -> SystemServiceExecutor:
    return SystemServiceExecutor(db=db)


TicketServiceDep = Annotated[TicketServiceExecutor, Depends(get_ticket_service)]
DashboardServiceDep = Annotated[DashboardServiceExecutor, Depends(get_dashboard_service)]
AuditServiceDep = Annotated[AuditServiceExecutor, Depends(get_audit_service)]
SystemServiceDep = Annotated[SystemServiceExecutor, Depends(get_system_service)]
