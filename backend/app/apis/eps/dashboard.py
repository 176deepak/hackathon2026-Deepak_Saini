from fastapi import APIRouter, Query, status

from app.core.dependencies import DashboardServiceDep
from app.schemas.api import (
    DashboardMetricsData, DashboardRecentActivityData, DashboardRecentActivityItem, 
    RESTResponse
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/metrics",
    response_model=RESTResponse[DashboardMetricsData],
    summary="Get dashboard metrics",
    description=(
        "Fetch dashboard counters including total tickets, resolved, escalated, and failed."
    ),
)
async def get_metrics(dashboard_service: DashboardServiceDep):
    metrics = await dashboard_service.get_metrics()

    return RESTResponse(
        code=status.HTTP_200_OK,
        success=True,
        data=DashboardMetricsData(
            total_tickets=metrics.total_tickets,
            resolved=metrics.resolved,
            escalated=metrics.escalated,
            failed=metrics.failed,
        ),
        msg="Dashboard metrics fetched successfully",
    )


@router.get(
    "/recent-activity",
    response_model=RESTResponse[DashboardRecentActivityData],
    summary="Get recent activity",
    description="Fetch latest ticket updates seen by the support agent.",
)
async def recent_activity(
    dashboard_service: DashboardServiceDep,
    limit: int = Query(default=10, ge=1, le=50, description="Max rows to return"),
):
    rows = await dashboard_service.get_recent_activity(limit=limit)
    return RESTResponse(
        code=status.HTTP_200_OK,
        success=True,
        data=DashboardRecentActivityData(
            items=[DashboardRecentActivityItem(**row) for row in rows]
        ),
        msg="Recent activity fetched successfully",
    )
