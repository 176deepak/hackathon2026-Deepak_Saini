from fastapi import APIRouter, status

from app.core.dependencies import SystemServiceDep
from app.schemas.api import RESTResponse, SystemHealthData, SystemPingData
from ..docs import SYSTEM_HEALTH_API_DOC, SYSTEM_PING_API_DOC

router = APIRouter(prefix="/system", tags=["System"])


@router.get(
    "/health",
    response_model=RESTResponse[SystemHealthData],
    summary="Health check"
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
    summary="Ping"
)
async def ping(system_service: SystemServiceDep):
    ping_payload = await system_service.ping()
    return RESTResponse(
        code=status.HTTP_200_OK,
        success=True,
        data=SystemPingData(**ping_payload),
        msg="Ping successful",
    )


health.__doc__ = SYSTEM_HEALTH_API_DOC
ping.__doc__ = SYSTEM_PING_API_DOC
