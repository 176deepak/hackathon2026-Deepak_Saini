import logging

from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.handlers.exceptions import http_exception_handler, unhandled_exception_handler
from app.utils import current_operation

from .logging import (
    LogCategory, LogEvent, LogLayer, LogStatus, AppLoggerAdapter, extra_,
)

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.CORE,
        "category": LogCategory.EXCEPTION,
        "component": __name__,
    },
)


def setup_exception_handlers(app: FastAPI) -> None:
    operation = current_operation()

    logger.debug(
        "Registering exception handlers",
        extra=extra_(
            operation=operation,
            status=LogStatus.START,
            event=LogEvent.EXCEPTION_HANDLER_REGISTER,
        ),
    )

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    logger.info(
        "Exception handlers registered",
        extra=extra_(
            operation=operation,
            status=LogStatus.SUCCESS,
            event=LogEvent.EXCEPTION_HANDLER_REGISTER,
        ),
    )
