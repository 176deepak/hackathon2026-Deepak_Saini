import logging
from fastapi import FastAPI

from app.apis.rest import rest_router
from app.utils import current_operation
from .logging import (
    LogCategory, LogEvent, LogLayer, LogStatus, AppLoggerAdapter, extra_,
)

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.CORE,
        "category": LogCategory.ROUTER,
        "component": __name__,
    },
)


def setup_routes(app: FastAPI) -> None:
    operation = current_operation()

    logger.debug(
        "REST API router registration started",
        extra=extra_(
            operation=operation,
            status=LogStatus.START,
            event=LogEvent.ROUTER_REGISTER
        )
    )

    app.include_router(rest_router)

    logger.info(
        "REST API router registered",
        extra=extra_(
            operation=operation,
            status=LogStatus.SUCCESS,
            event=LogEvent.ROUTER_REGISTER
        )
    )
