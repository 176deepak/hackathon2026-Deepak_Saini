import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.clients import init_postgres
from .logging import AppLoggerAdapter, LogCategory, LogLayer
from .scheduler import scheduler

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.LIFESPAN,
        "category": LogCategory.LIFESPAN,
        "component": __name__,
    },
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        
        logger.debug("Initializing PostgreSQL")

        await init_postgres()

        logger.info("PostgreSQL initialized")

        if not scheduler.running:
            logger.debug("Starting scheduler")

            scheduler.start()

            logger.info("Scheduler started")

        else:
            logger.warning("Scheduler already running")
            
    except Exception:
        logger.exception("Application startup failed")
        raise

    yield