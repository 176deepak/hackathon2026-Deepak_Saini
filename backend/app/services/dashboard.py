from app.repositories.base import BaseDashboardRepo
from app.schemas.repo import DashboardMetrics
from app.services.base import BaseDashboardService


class DashboardService(BaseDashboardService):
    def __init__(self, dashboard_repo: BaseDashboardRepo):
        super().__init__(dashboard_repo=dashboard_repo)

    def get_metrics(self) -> DashboardMetrics:
        return self.dashboard_repo.get_metrics()

    def get_recent_activity(self, limit: int = 10) -> list[dict]:
        return self.dashboard_repo.get_recent_activity(limit=limit)
