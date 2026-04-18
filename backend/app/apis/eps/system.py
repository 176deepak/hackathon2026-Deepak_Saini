from fastapi import APIRouter, status

from app.core.dependencies import SystemServiceDep
from app.schemas.api import RESTResponse, SystemHealthData, SystemPingData

router = APIRouter(prefix="/system", tags=["System"])


@router.get(
    "/health",
    response_model=RESTResponse[SystemHealthData],
    summary="Health check",
    description="Readiness endpoint that validates service + database connectivity.",
)
async def health(system_service: SystemServiceDep):
    health_payload = await system_service.check_health()

    return RESTResponse(
        code=status.HTTP_200_OK,
        success=True,
        data=SystemHealthData(**health_payload),
        msg="System healthy",
    )


@router.get(
    "/ping",
    response_model=RESTResponse[SystemPingData],
    summary="Ping",
    description="Liveness endpoint for lightweight checks.",
)
async def ping(system_service: SystemServiceDep):
    ping_payload = await system_service.ping()
    return RESTResponse(
        code=status.HTTP_200_OK,
        success=True,
        data=SystemPingData(**ping_payload),
        msg="Ping successful",
    )
