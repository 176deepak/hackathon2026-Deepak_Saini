import logging
from app.repositories.base import BaseDashboardRepo
from app.schemas.repo import DashboardMetrics
from app.services.base import BaseDashboardService
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.SERVICE,
        "category": LogCategory.API,
        "component": __name__,
    },
)


class DashboardService(BaseDashboardService):
    def __init__(self, dashboard_repo: BaseDashboardRepo):
        super().__init__(dashboard_repo=dashboard_repo)

    def get_metrics(self) -> DashboardMetrics:
        try:
            metrics = self.dashboard_repo.get_metrics()
            logger.debug(
                "Dashboard metrics returned",
                extra=extra_(operation="svc_dashboard_metrics", status="success"),
            )
            return metrics
        except Exception:
            logger.exception(
                "Failed to get dashboard metrics",
                extra=extra_(operation="svc_dashboard_metrics", status="failure"),
            )
            raise

    def get_recent_activity(self, limit: int = 10) -> list[dict]:
        try:
            rows = self.dashboard_repo.get_recent_activity(limit=limit)
            logger.debug(
                "Dashboard recent activity returned",
                extra=extra_(
                    operation="svc_dashboard_recent_activity",
                    status="success",
                    limit=limit,
                    count=len(rows),
                ),
            )
            return rows
        except Exception:
            logger.exception(
                "Failed to get recent activity",
                extra=extra_(
                    operation="svc_dashboard_recent_activity",
                    status="failure",
                    limit=limit,
                ),
            )
            raise
