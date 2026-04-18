import logging

from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.handlers.exceptions import http_exception_handler, unhandled_exception_handler
from .logging import LogCategory, LogLayer, AppLoggerAdapter

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.EXCEPTION,
        "category": LogCategory.EXCEPTION,
        "component": __name__,
    },
)


def setup_exception_handlers(app: FastAPI) -> None:
    logger.debug("Registering exception handlers")

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    logger.info("Exception handlers registered")
