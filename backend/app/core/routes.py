import logging
from fastapi import FastAPI

from app.apis import rest_router
from .logging import LogCategory, LogLayer, AppLoggerAdapter

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.ROUTER,
        "category": LogCategory.ROUTER,
        "component": __name__,
    },
)


def setup_routes(app: FastAPI) -> None:
    logger.debug("REST API router registration started")

    app.include_router(rest_router)

    logger.info("REST API router registered")
